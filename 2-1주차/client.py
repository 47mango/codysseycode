#!/usr/bin/env python3
"""
단순 콘솔 클라이언트 (표준 라이브러리만 사용)
- 읽기/쓰기 스레드 분리
- "/종료" 입력 시 종료
"""
from __future__ import annotations

import argparse
import socket
import sys
import threading


def reader(sock: socket.socket) -> None:
    try:
        rfile = sock.makefile("r", encoding="utf-8", errors="replace", newline="\n")
        for line in rfile:
            print(line.rstrip("\n"))
    except Exception:
        pass
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        sock.close()


def writer(sock: socket.socket) -> None:
    wfile = sock.makefile("w", encoding="utf-8", errors="replace", newline="\n")
    try:
        while True:
            try:
                line = input()
            except EOFError:
                break
            wfile.write(line + "\n")
            wfile.flush()
            if line.strip() in ("/종료", "/quit", "/exit"):
                break
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        sock.close()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="단순 채팅 클라이언트")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.port))

    t_r = threading.Thread(target=reader, args=(sock,), daemon=True)
    t_r.start()
    writer(sock)
    t_r.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
