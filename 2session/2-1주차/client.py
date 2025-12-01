#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import argparse
import sys

def recv_loop(sock: socket.socket) -> None:
    try:
        rfile = sock.makefile("r", encoding="utf-8", newline="\n")
        for line in rfile:
            msg = line.rstrip("\n")
            print(msg)
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except OSError:
            pass
        # 수신 스레드가 끝나면 프로세스도 종료되도록 안내
        print("SYS> 서버와의 연결이 종료되었습니다.")
        # 입력 대기 중일 수 있으므로 stdout flush
        sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="TCP 채팅 클라이언트")
    parser.add_argument("--host", default="127.0.0.1", help="서버 호스트 (기본: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5060, help="서버 포트 (기본: 5060)")
    parser.add_argument("--name", help="닉네임(옵션). 미지정 시 실행 후 물어봄.")
    args = parser.parse_args()

    if not args.name:
        try:
            args.name = input("닉네임을 입력하세요: ").strip()
        except EOFError:
            print("닉네임이 필요합니다.")
            return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((args.host, args.port))
    except ConnectionRefusedError:
        print("SYS> 서버에 접속할 수 없습니다. 서버가 켜져있는지/포트가 맞는지 확인하세요.")
        return

    # 첫 줄에 닉네임 전송 (프로토콜)
    try:
        sock.sendall(("NICK " + args.name + "\n").encode("utf-8"))
    except OSError:
        print("SYS> 닉네임 전송 실패")
        return

    # 수신 스레드 시작
    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    print("SYS> 명령어: /종료, /list, /help, /w 대상닉 메시지, @대상닉 메시지")
    try:
        while True:
            try:
                line = input()
            except EOFError:
                line = "/종료"
            line = line.strip()
            if not line:
                continue

            try:
                sock.sendall((line + "\n").encode("utf-8"))
            except OSError:
                break

            if line == "/종료":
                break
    except KeyboardInterrupt:
        try:
            sock.sendall(("/종료\n").encode("utf-8"))
        except OSError:
            pass
    finally:
        try:
            sock.close()
        except OSError:
            pass

if __name__ == "__main__":
    main()
