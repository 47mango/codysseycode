#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import argparse
from typing import Dict, Tuple

Address = Tuple[str, int]

class ChatServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 재시작 시 "Address already in use" 최소화
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # name -> (conn, addr)
        self.clients: Dict[str, Tuple[socket.socket, Address]] = {}
        self.lock = threading.Lock()

    def start(self) -> None:
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen()
        print(f"[서버] {self.host}:{self.port} 에서 대기 중...")

        try:
            while True:
                conn, addr = self.server_sock.accept()
                threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[서버] 종료 신호 감지. 서버를 종료합니다.")
        finally:
            with self.lock:
                for name, (c, _) in list(self.clients.items()):
                    try:
                        c.close()
                    except OSError:
                        pass
                self.clients.clear()
            self.server_sock.close()

    # ---------- 내부 유틸 ----------
    def _send_text(self, conn: socket.socket, text: str) -> None:
        try:
            conn.sendall((text + "\n").encode("utf-8"))
        except OSError:
            pass

    def _broadcast(self, text: str, exclude: str = None) -> None:
        """모든 클라이언트에게 방송(옵션: 특정 닉 제외)."""
        dead = []
        with self.lock:
            for name, (conn, _) in self.clients.items():
                if exclude and name == exclude:
                    continue
                try:
                    conn.sendall((text + "\n").encode("utf-8"))
                except OSError:
                    dead.append(name)
            for name in dead:
                conn, _ = self.clients.pop(name, (None, None))
                if conn:
                    try:
                        conn.close()
                    except OSError:
                        pass

    def _make_unique_name(self, base: str) -> str:
        base = (base or "user").strip()
        if not base:
            base = "user"
        base = "_".join(base.split())  # 공백 -> _
        name = base
        idx = 1
        with self.lock:
            while name in self.clients:
                idx += 1
                name = f"{base}_{idx}"
        return name

    # ---------- 클라이언트 처리 ----------
    def _handle_client(self, conn: socket.socket, addr: Address) -> None:
        rfile = conn.makefile("r", encoding="utf-8", newline="\n")

        # 1) 닉네임 수신 (첫 줄은 반드시 닉네임)
        try:
            first_line = rfile.readline()
        except Exception:
            conn.close()
            return

        if not first_line:
            conn.close()
            return

        first_line = first_line.strip()
        if first_line.upper().startswith("NICK "):
            requested_name = first_line[5:].strip()
        else:
            # 호환: 그냥 닉네임만 보내온 경우
            requested_name = first_line.strip()

        name = self._make_unique_name(requested_name)
        with self.lock:
            self.clients[name] = (conn, addr)

        # 개인 환영 메세지 & 전체 입장 방송
        self._send_text(conn, f"SYS> 서버에 연결되었습니다. 닉네임: {name}")
        if name != requested_name:
            self._send_text(conn, f"SYS> 요청한 닉네임이 사용 중이어서 '{name}' 로 설정했습니다.")
        self._broadcast(f"{name}님이 입장하셨습니다.")

        try:
            for line in rfile:
                msg = line.rstrip("\n").strip()
                if not msg:
                    continue

                # 종료
                if msg == "/종료":
                    break

                # 유저 리스트
                if msg == "/list":
                    with self.lock:
                        users = ", ".join(sorted(self.clients.keys()))
                    self._send_text(conn, f"SYS> 현재 접속자: {users}")
                    continue

                # 도움말
                if msg in ("/help", "/도움말"):
                    self._send_text(conn, "SYS> 명령어: /종료, /list, /help, /w 대상닉 메시지, @대상닉 메시지")
                    continue

                # 귓속말: /w 대상닉 메시지
                if msg.startswith("/w "):
                    parts = msg.split(maxsplit=2)
                    if len(parts) < 3:
                        self._send_text(conn, "SYS> 사용법: /w 대상닉 메시지")
                        continue
                    target, content = parts[1], parts[2]
                    self._whisper(name, target, content, conn)
                    continue

                # 귓속말: @대상닉 메시지
                if msg.startswith("@"):
                    if " " not in msg:
                        self._send_text(conn, "SYS> 사용법: @대상닉 메시지")
                        continue
                    target, content = msg[1:].split(" ", 1)
                    self._whisper(name, target.strip(), content.strip(), conn)
                    continue

                # 일반 방송
                self._broadcast(f"{name}> {msg}")
        except Exception:
            # 연결 중 예외는 무시하고 정리
            pass
        finally:
            # 종료 처리
            with self.lock:
                self.clients.pop(name, None)
            try:
                conn.close()
            except OSError:
                pass
            self._broadcast(f"{name}님이 퇴장하셨습니다.")

    def _whisper(self, sender: str, target: str, content: str, sender_conn: socket.socket) -> None:
        with self.lock:
            entry = self.clients.get(target)
        if not entry:
            self._send_text(sender_conn, f"SYS> '{target}' 닉네임을 가진 사용자가 없습니다.")
            return

        target_conn, _ = entry
        # 수신자에게
        self._send_text(target_conn, f"(귓속말) {sender}> {content}")
        # 보낸 사람에게도 확인 메세지
        self._send_text(sender_conn, f"(귓속말 to {target}) {sender}> {content}")


def main():
    parser = argparse.ArgumentParser(description="멀티스레드 TCP 채팅 서버")
    parser.add_argument("--host", default="0.0.0.0", help="바인드 호스트 (기본: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5060, help="포트 (기본: 5060)")
    args = parser.parse_args()

    ChatServer(args.host, args.port).start()


if __name__ == "__main__":
    main()
