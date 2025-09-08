#!/usr/bin/env python3
"""
멀티스레드 TCP 채팅 서버 (표준 라이브러리만 사용)
- 접속 시 닉네임 등록 (공백 없는 2~20자)
- 입장/퇴장 방송
- 일반 메시지 브로드캐스트: "닉네임> 메시지"
- 종료 명령: "/종료"
- 귓속말: "/w 대상닉 메시지" (별칭: "/whisper", "/귓속말")
- 현재 접속자 목록: "/list"
"""

from __future__ import annotations

import argparse
import re
import socket
import threading
from typing import Dict, Tuple, TextIO


Nickname = str
ClientInfo = Tuple[socket.socket, TextIO]  # (conn, writer-like file)


class ChatServer:
    """멀티스레드 채팅 서버 구현."""

    NICK_PATTERN = re.compile(r"^\S{2,20}$")  # 공백 없는 2~20자

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._lock = threading.Lock()
        self._clients: Dict[Nickname, ClientInfo] = {}  # 닉네임: (conn, wfile)

        self._running = threading.Event()
        self._running.set()

    # ---------- 서버 수명주기 ----------

    def start(self) -> None:
        """서버 시작 및 메인 accept 루프."""
        self._srv_sock.bind((self.host, self.port))
        self._srv_sock.listen()
        print(f"[서버] {self.host}:{self.port} 에서 대기중... (Ctrl+C 종료)")

        try:
            while self._running.is_set():
                conn, addr = self._srv_sock.accept()
                t = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True,
                )
                t.start()
        except KeyboardInterrupt:
            print("\n[서버] 종료 요청 수신, 정리 중...")
        finally:
            self._shutdown()

    def _shutdown(self) -> None:
        """서버 자원 정리."""
        self._running.clear()
        with self._lock:
            for nick, (conn, wfile) in list(self._clients.items()):
                try:
                    self._safe_send(wfile, "[서버] 서버가 종료됩니다.\n")
                except Exception:
                    pass
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                conn.close()
            self._clients.clear()
        try:
            self._srv_sock.close()
        except Exception:
            pass
        print("[서버] 정상 종료")

    # ---------- 클라이언트 처리 ----------

    def _handle_client(self, conn: socket.socket, addr: Tuple[str, int]) -> None:
        """신규 클라이언트 연결 처리."""
        rfile = conn.makefile("r", encoding="utf-8", errors="replace", newline="\n")
        wfile = conn.makefile("w", encoding="utf-8", errors="replace", newline="\n")

        try:
            nick = self._handshake_for_nickname(rfile, wfile)
            if not nick:
                return

            # 등록
            with self._lock:
                self._clients[nick] = (conn, wfile)

            self._broadcast_system(f"{nick}님이 입장하셨습니다.\n")

            # 안내
            self._safe_send(
                wfile,
                "안내: 일반 메시지는 모두에게 전송됩니다.\n"
                "명령: /종료, /list, /w 닉 메시지, /whisper 닉 메시지, /귓속말 닉 메시지\n",
            )

            # 메시지 루프
            for line in rfile:
                msg = line.strip()
                if not msg:
                    continue

                if msg.startswith("/"):
                    if self._handle_command(nick, msg):
                        # True 반환 시 연결 종료 의사(/종료)
                        break
                else:
                    # 일반 메시지 브로드캐스트
                    self._broadcast_chat(nick, msg)
        except Exception as exc:
            print(f"[서버] 예외({addr}): {exc}")
        finally:
            self._remove_client(nick if "nick" in locals() else None)

            try:
                rfile.close()
            except Exception:
                pass
            try:
                wfile.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    def _handshake_for_nickname(self, rfile: TextIO, wfile: TextIO) -> str | None:
        """닉네임 입력/검증 후 반환. 실패 시 None."""
        attempts = 0
        while attempts < 5:
            self._safe_send(wfile, "닉네임을 입력하세요 (공백 없이 2~20자): ")
            nick = rfile.readline()
            if not nick:
                return None
            nick = nick.strip()

            if not self.NICK_PATTERN.match(nick):
                self._safe_send(wfile, "[서버] 형식이 올바르지 않습니다.\n")
                attempts += 1
                continue

            with self._lock:
                if nick in self._clients:
                    self._safe_send(wfile, "[서버] 이미 사용 중인 닉네임입니다.\n")
                    attempts += 1
                    continue
            return nick

        self._safe_send(wfile, "[서버] 닉네임 시도 횟수 초과. 연결을 종료합니다.\n")
        return None

    # ---------- 브로드캐스트 & 전송 ----------

    def _broadcast_system(self, text: str) -> None:
        """시스템 메시지 방송."""
        with self._lock:
            for _nick, (_conn, wfile) in list(self._clients.items()):
                self._safe_send(wfile, f"[시스템] {text}")

    def _broadcast_chat(self, nick: str, message: str) -> None:
        """일반 채팅 메시지 방송."""
        line = f"{nick}> {message}\n"
        with self._lock:
            for _nick, (_conn, wfile) in list(self._clients.items()):
                self._safe_send(wfile, line)

    def _send_to(self, nick: str, line: str) -> bool:
        """특정 닉네임에게만 전송. 성공 여부 반환."""
        with self._lock:
            info = self._clients.get(nick)
            if not info:
                return False
            _conn, wfile = info
            self._safe_send(wfile, line)
            return True

    @staticmethod
    def _safe_send(wfile: TextIO, text: str) -> None:
        """줄 단위 안전 전송."""
        try:
            wfile.write(text)
            wfile.flush()
        except Exception:
            # 상대방이 끊었을 수 있음. 상위에서 정리.
            pass

    # ---------- 명령 처리 ----------

    def _handle_command(self, sender: str, raw: str) -> bool:
        """명령어 처리. True 반환 시 연결 종료 의사."""
        parts = raw.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd in ("/종료", "/quit", "/exit"):
            self._send_to(sender, "[서버] 연결을 종료합니다.\n")
            return True

        if cmd == "/list":
            with self._lock:
                users = ", ".join(sorted(self._clients.keys()))
            self._send_to(sender, f"[서버] 현재 접속자: {users}\n")
            return False

        if cmd in ("/w", "/whisper", "/귓속말"):
            if len(parts) < 3:
                self._send_to(sender, "[서버] 사용법: /w 대상닉 메시지\n")
                return False
            target = parts[1]
            msg = parts[2]
            if target == sender:
                self._send_to(sender, "[서버] 자기 자신에게는 귓속말을 보낼 수 없습니다.\n")
                return False

            sent = self._send_to(target, f"[귓속말]<-{sender}> {msg}\n")
            if not sent:
                self._send_to(sender, "[서버] 대상 닉네임이 존재하지 않습니다.\n")
            else:
                self._send_to(sender, f"[귓속말]->{target}> {msg}\n")
            return False

        # 알 수 없는 명령
        self._send_to(
            sender,
            "[서버] 알 수 없는 명령입니다. (/list, /w, /종료)\n",
        )
        return False

    # ---------- 클라이언트 정리 ----------

    def _remove_client(self, nick: str | None) -> None:
        """클라이언트 사전에서 제거 및 퇴장 방송."""
        if not nick:
            return
        with self._lock:
            removed = self._clients.pop(nick, None)
        if removed:
            self._broadcast_system(f"{nick}님이 퇴장하셨습니다.\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="멀티스레드 TCP 채팅 서버")
    parser.add_argument("--host", default="0.0.0.0", help="바인드 호스트 (기본: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="포트 (기본: 5000)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ChatServer(args.host, args.port)
    server.start()


if __name__ == "__main__":
    main()
