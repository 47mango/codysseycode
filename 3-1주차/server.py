#!/usr/bin/env python3
# server.py
import os
import json
import datetime
import http.server
import socketserver
import ipaddress
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

PORT = 8080
INDEX_FILE = "3-1주차/index.html"

SPACE_PIRATE_HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>우주 해적 소개</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", Arial, sans-serif;
           line-height: 1.6; margin: 0; padding: 2rem; background: #0b1020; color: #eef2ff; }
    .card { max-width: 880px; margin: 0 auto; background: #111832; border-radius: 16px; padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,.35); }
    h1 { margin-top: 0; font-size: 2rem; }
    h2 { margin-top: 2rem; font-size: 1.3rem; color: #a5b4fc; }
    p { color: #dbe4ff; }
    .meta { margin-top: 2rem; font-size: .9rem; color: #9aa4c8; }
    code { background: rgba(255,255,255,0.08); padding: .2rem .4rem; border-radius: 6px; }
    a { color: #93c5fd; }
  </style>
</head>
<body>
  <div class="card">
    <h1>⚓️ 우주 해적(宇宙海賊) 소개</h1>
    <p>
      우주 해적은 광활한 성간 항로를 누비며 금지된 유물과 희귀 자원을 노리는 전설의 무리입니다.
      그들은 최첨단 함선에 탑승해 게릴라식 전술과 교란 장치를 활용하고,
      항법 데이터를 탈취해 초공간 항로를 선점합니다.
    </p>
    <h2>주요 특징</h2>
    <ul>
      <li>스텔스 필드로 레이더를 회피하는 <strong>클로킹 전술</strong></li>
      <li>상대 항성계의 규약을 역이용하는 <strong>교란 작전</strong></li>
      <li>드론과 보조 AI를 활용한 <strong>원격 약탈/구출 임무</strong></li>
    </ul>
    <h2>윤리 규범</h2>
    <p>
      전설 속 우주 해적은 무차별 파괴를 지양하고, 억압적 지배에 맞선 균형자 역할을 자처하기도 합니다.
      이는 그들이 단순한 악당이 아니라, 체제의 그늘을 건너는 <em>경계인</em>임을 보여줍니다.
    </p>
    <div class="meta">
      이 페이지는 <code>http.server</code>로 구동되는 예시 서버에서 제공됩니다.
    </div>
  </div>
</body>
</html>
"""

def ensure_index_file():
    """index.html이 없으면 우주 해적 소개 페이지를 생성합니다."""
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(SPACE_PIRATE_HTML)

def is_private_or_local(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local
    except ValueError:
        return True  # 이상한 값이면 조회하지 않음

def geolocate_ip(ip: str):
    """
    공개 API(ip-api.com)를 사용해 대략적 위치 정보를 조회합니다.
    - 사설/로컬 IP는 조회하지 않습니다.
    - 반환: dict 또는 None
    """
    if is_private_or_local(ip):
        return None

    url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,query,message"
    req = Request(url, headers={"User-Agent": "Python-urllib/3 http.server demo"})
    try:
        with urlopen(req, timeout=5) as resp:
            data = json.load(resp)
            if data.get("status") == "success":
                return {
                    "ip": data.get("query"),
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "isp": data.get("isp"),
                }
            else:
                return None
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

class SimpleHandler(http.server.BaseHTTPRequestHandler):
    server_version = "SimpleHTTPGeo/1.0"

    def log_message(self, format, *args):
        # 기본 로그 포맷 대신 깔끔하게 출력(필요 시 원본 유지 가능)
        print("%s - - %s" % (self.address_string(),
              format % args))

    def _client_ip(self) -> str:
        # 프록시를 통해 온 경우 X-Forwarded-For를 우선 고려(콤마로 구분되는 첫 IP 사용)
        fwd = self.headers.get("X-Forwarded-For")
        if fwd:
            return fwd.split(",")[0].strip()
        return self.client_address[0]

    def do_GET(self):
        # 1) 접속 정보 수집
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_ip = self._client_ip()
        ua = self.headers.get("User-Agent", "-")

        # 2) 위치 정보 조회(사설/로컬 IP면 스킵)
        geo = geolocate_ip(client_ip)

        # 3) 서버 콘솔 출력
        print("========================================")
        print(f"접속 시간: {now}")
        print(f"클라이언트 IP: {client_ip}")
        print(f"User-Agent: {ua}")
        if geo:
            print(f"대략적 위치: {geo.get('country', '-')}, {geo.get('region', '-')}, {geo.get('city', '-')}")
            print(f"ISP: {geo.get('isp', '-')}")
        else:
            print("위치 정보: (사설/로컬 IP 또는 조회 실패)")

        # 4) index.html 제공
        ensure_index_file()
        try:
            with open(INDEX_FILE, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            body = b"<h1>index.html not found</h1>"

        # 5) 응답: 200 OK + 헤더
        self.send_response(200)  # 성공 코드
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def run():
    ensure_index_file()
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), SimpleHandler) as httpd:
        print(f"서버 시작: http://localhost:{PORT}  (Ctrl+C 로 종료)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버 종료 중...")
        finally:
            httpd.server_close()
            print("서버가 종료되었습니다.")

if __name__ == "__main__":
    run()
