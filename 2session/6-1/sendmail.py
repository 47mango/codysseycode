#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sendmail.py — Send email via Gmail's SMTP with SSL (465) or STARTTLS (587).

✔ What this script covers (aligned to your checklist):
1) "본인의 Gmail 계정을 확인한다" → Prints/validates the sender account and domain.
2) "SMTP 기본 포트 넘버" → Defaults to 465 (SSL). Optionally use 587 with --starttls.
3) "SMTP 패키지 선택/설치" → Uses Python stdlib: smtplib, ssl, email. Optional: python-dotenv for .env support.
4) "보내는 사람/받는 사람 설정" → CLI args & environment variables.
5) "보내는 사람 비밀번호 설정" → Reads from env (GMAIL_APP_PASSWORD) or secure prompt.
   ※ Gmail은 일반 비밀번호가 아니라 '앱 비밀번호(App Password)'를 권장합니다. (2단계 인증 필요)
6) "SMTP 로그인 후 메일 전송" → Handles SSL or STARTTLS flows.
7) "예외 처리" → Detailed error handling with helpful messages.
8) "파일로 저장" → This file is already named sendmail.py.

USAGE EXAMPLES
--------------
# .env (optional, same folder)
# GMAIL_USER="your.name@gmail.com"
# GMAIL_APP_PASSWORD="abcd efgh ijkl mnop"

# Simple text email (SSL 465, default)
python3 sendmail.py --to someone@example.com --subject "테스트" --body "안녕하세요!"

# Use STARTTLS (587)
python3 sendmail.py --to a@ex.com,b@ex.com --subject "Hello" --body "Hi" --starttls

# Override sender (else .env GMAIL_USER)
python3 sendmail.py --from you@gmail.com --to me@ex.com --subject "From override" --body "..."

# Prompt for password if env not set
python3 sendmail.py --to me@ex.com --subject "pw prompt" --body "..."

# Add CC / BCC
python3 sendmail.py --to to@ex.com --cc cc@ex.com --bcc b1@ex.com,b2@ex.com --subject S --body B

# Send HTML
python3 sendmail.py --to to@ex.com --subject S --html "<h1>굿</h1><p>HTML 본문</p>"
"""

import argparse
import os
import re
import smtplib
import socket
import ssl
from email.message import EmailMessage
from getpass import getpass
from typing import List, Optional

# Optional: load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

GMAIL_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SSL_PORT = 465   # SMTPS (implicit SSL)
DEFAULT_TLS_PORT = 587   # STARTTLS

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def parse_recipients(value: str) -> List[str]:
    parts = [x.strip() for x in value.split(",") if x.strip()]
    for p in parts:
        if not EMAIL_RE.match(p):
            raise argparse.ArgumentTypeError(f"잘못된 이메일 형식: {p}")
    return parts


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Send email via Gmail SMTP (SSL 465 or STARTTLS 587).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--from", dest="sender", default=os.getenv("GMAIL_USER"),
                   help="보내는 사람 이메일 (기본: 환경변수 GMAIL_USER)")
    p.add_argument("--to", required=True, type=parse_recipients,
                   help="받는 사람 이메일(들), 콤마로 구분")
    p.add_argument("--cc", type=parse_recipients, default=[],
                   help="CC 이메일(들), 콤마로 구분")
    p.add_argument("--bcc", type=parse_recipients, default=[],
                   help="BCC 이메일(들), 콤마로 구분")

    p.add_argument("--subject", required=True, help="메일 제목")
    body_group = p.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="텍스트 본문")
    body_group.add_argument("--html", help="HTML 본문")

    p.add_argument("--server", default=GMAIL_SMTP_SERVER, help="SMTP 서버 주소")
    p.add_argument("--port", type=int, default=DEFAULT_SSL_PORT, help="SMTP 포트")
    p.add_argument("--starttls", action="store_true",
                   help="STARTTLS(587) 사용 (명시 시 기본 포트를 587로 변경)")
    p.add_argument("--sender-name", default=None, help="보내는 사람 이름 (표시용)")
    p.add_argument("--reply-to", default=None, help="Reply-To 주소")
    p.add_argument("--dry-run", action="store_true", help="실제 전송 없이 구성만 출력")
    return p


def validate_sender(sender: Optional[str]) -> str:
    if not sender:
        raise SystemExit("보내는 사람 이메일이 필요합니다. --from 또는 환경변수 GMAIL_USER 를 설정하세요.")
    sender = sender.strip()
    if not EMAIL_RE.match(sender):
        raise SystemExit(f"보내는 사람 이메일 형식이 잘못되었습니다: {sender}")
    # Soft check: Gmail domain (can still work for Google Workspace)
    domain = sender.split("@")[-1].lower()
    if "gmail.com" not in domain and "googlemail.com" not in domain:
        print(f"[경고] Gmail 도메인으로 보이지 않습니다: {sender} (Google Workspace라면 정상일 수 있습니다)")
    return sender


def get_password_interactive_if_needed() -> str:
    pw = os.getenv("GMAIL_APP_PASSWORD")
    if pw and pw.strip():
        return pw.strip()
    # Fallback: prompt
    print("환경변수 GMAIL_APP_PASSWORD 가 설정되지 않았습니다.")
    print("Gmail 앱 비밀번호를 입력하세요 (일반 비밀번호가 아님):")
    return getpass("App Password: ")


def build_message(sender: str,
                  to: List[str],
                  subject: str,
                  text_body: Optional[str],
                  html_body: Optional[str],
                  cc: Optional[List[str]] = None,
                  bcc: Optional[List[str]] = None,
                  sender_name: Optional[str] = None,
                  reply_to: Optional[str] = None) -> EmailMessage:
    msg = EmailMessage()
    from_display = f"{sender_name} <{sender}>" if sender_name else sender
    msg["From"] = from_display
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Subject"] = subject

    if html_body:
        # Add both plain text (fallback) and HTML if only HTML provided
        alt_text = text_body if text_body else "This is an HTML email. Your client may not support HTML."
        msg.set_content(alt_text)
        msg.add_alternative(html_body, subtype="html")
    else:
        msg.set_content(text_body or "")

    # Note: BCC is added in the envelope only (not header)
    return msg


def send_via_gmail(sender: str,
                   app_password: str,
                   msg: EmailMessage,
                   server: str,
                   port: int,
                   use_starttls: bool,
                   to: List[str],
                   cc: List[str],
                   bcc: List[str]) -> None:
    all_rcpts = list(dict.fromkeys(to + (cc or []) + (bcc or [])))  # dedupe while preserving order

    if use_starttls:
        # STARTTLS on 587
        context = ssl.create_default_context()
        with smtplib.SMTP(server, port, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(sender, app_password)
            smtp.send_message(msg, from_addr=sender, to_addrs=all_rcpts)
    else:
        # Implicit SSL on 465
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(server, port, context=context, timeout=20) as smtp:
            smtp.login(sender, app_password)
            smtp.send_message(msg, from_addr=sender, to_addrs=all_rcpts)


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Adjust port if --starttls used and user didn't override port
    if args.starttls and args.port == DEFAULT_SSL_PORT:
        args.port = DEFAULT_TLS_PORT

    sender = validate_sender(args.sender)
    print(f"[계정 확인] 보내는 계정: {sender}")
    print(f"[SMTP 설정] server={args.server}, port={args.port}, mode={'STARTTLS' if args.starttls else 'SSL'}")

    password = get_password_interactive_if_needed()

    # Build message
    msg = build_message(
        sender=sender,
        to=args.to,
        subject=args.subject,
        text_body=args.body,
        html_body=args.html,
        cc=args.cc,
        bcc=args.bcc,
        sender_name=args.sender_name,
        reply_to=args.reply_to,
    )

    if args.dry_run:
        print("[DRY RUN] 실제 전송하지 않습니다.")
        print("헤더:")
        for k, v in msg.items():
            print(f"  {k}: {v}")
        print("본문 미리보기:")
        payload = msg.get_body(preferencelist=("html", "plain"))
        print(payload.get_content()[:300] + ("..." if len(payload.get_content()) > 300 else ""))
        return

    # Send with detailed error handling
    try:
        send_via_gmail(
            sender=sender,
            app_password=password,
            msg=msg,
            server=args.server,
            port=args.port,
            use_starttls=args.starttls,
            to=args.to,
            cc=args.cc or [],
            bcc=args.bcc or [],
        )
        print("✅ 메일 전송 성공")
    except smtplib.SMTPAuthenticationError as e:
        print("❌ 인증 실패: SMTPAuthenticationError")
        print(" - Gmail은 일반 비밀번호 대신 '앱 비밀번호'가 필요합니다.")
        print(" - Google 계정에서 2단계 인증을 켜고 앱 비밀번호를 생성해 주세요.")
        print(f" - details: {e}")
    except smtplib.SMTPRecipientsRefused as e:
        print("❌ 수신자 거부: SMTPRecipientsRefused")
        for rcpt, (code, resp) in e.recipients.items():
            print(f" - {rcpt}: {code} {resp}")
    except smtplib.SMTPSenderRefused as e:
        print("❌ 발신자 거부: SMTPSenderRefused")
        print(f" - {e.smtp_code} {e.smtp_error}")
        print(" - 보낸 사람 주소 또는 인증 상태를 확인하세요.")
    except smtplib.SMTPDataError as e:
        print("❌ 데이터 오류: SMTPDataError")
        print(f" - {e.smtp_code} {e.smtp_error}")
    except smtplib.SMTPConnectError as e:
        print("❌ 연결 실패: SMTPConnectError")
        print(f" - {e.smtp_code} {e.smtp_error}")
        print(" - 네트워크/방화벽/프록시 설정을 확인하세요.")
    except (socket.gaierror, TimeoutError) as e:
        print("❌ 네트워크 오류: 호스트 이름 확인 실패 또는 타임아웃")
        print(f" - details: {e}")
    except smtplib.SMTPException as e:
        print("❌ 일반 SMTP 예외 발생")
        print(f" - details: {e}")
    except Exception as e:
        print("❌ 알 수 없는 오류 발생")
        print(f" - details: {e}")


if __name__ == "__main__":
    main()
