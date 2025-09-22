#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawling_KBS.py

요구사항
- KBS(http://news.kbs.co.kr) 주요 헤드라인을 가져온다 (BeautifulSoup 사용, List에 저장 후 출력)
- 날씨 혹은 주식 가격 등 다른 사이트에서 필요한 정보도 함께 가져오는 서브커맨드 제공
- 완성된 코드는 argparse로 명령을 선택해서 실행 (kbs | weather | stock)

사전 준비
- 패키지 설치(맥/리눅스/윈도우 공통):
    python3 -m pip install requests beautifulsoup4

DevTools로 셀렉터 찾는 팁 (KBS 헤드라인)
1) 브라우저에서 https://news.kbs.co.kr 접속
2) 헤드라인 영역의 기사 제목 텍스트를 우클릭 → '검사(Inspect)'
3) <a> 링크(기사 제목)를 감싼 요소의 "고유한" CSS 셀렉터를 복사(Copy selector)
4) 아래 SELECTOR_HEADLINES 에 붙여 넣고 실행
   (예: 'section.headline a.tit', 'div#headline a', 사이트 구조에 따라 다릅니다)

주의
- 실제 뉴스 사이트는 구조와 셀렉터가 자주 바뀝니다. 아래 코드는 기본/폴백 셀렉터를 여러 개 시도합니다.
- 일부 사이트는 봇 접근을 막습니다. User-Agent 헤더 추가 및 예외 처리를 해두었습니다.
- 교육용 예제이며, 상업적 대량 수집 전에는 각 사이트의 robots.txt 및 이용약관을 반드시 확인하세요.
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

# 공통 요청 헤더 (간단한 브라우저 흉내)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# -----------------------------
# 1) KBS 헤드라인 크롤링
# -----------------------------

# DevTools에서 확인 후 이 값을 본인 환경에 맞게 업데이트하세요.
# 예시 후보들을 아래 DEFAULT_FALLBACK_SELECTORS 에서 순차 시도합니다.
SELECTOR_HEADLINES: Optional[str] = None

# 사이트 구조 변화에 대비한 폴백 셀렉터 후보들(필요할 때 추가/수정)
DEFAULT_FALLBACK_SELECTORS: List[str] = [
    "section.headline a",          # 예시: 섹션에 headline 클래스가 있을 경우
    "#headline a",                 # 예시: id가 headline인 컨테이너
    "div.headline a",
    "ul#headline a",
    "div.top-news a",
    "a.headline",                  # 제목 링크 자체에 headline 클래스가 붙은 경우
    "dt a",                        # 일부 포털형 리스트
    "h2 a, h3 a"                   # 제목이 h2/h3로 마크업된 경우
]

def fetch_kbs_headlines(limit: int = 10, url: str = "https://news.kbs.co.kr") -> List[str]:
    """KBS 메인에서 헤드라인 텍스트를 수집하여 리스트로 반환."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        raise SystemExit(f"[KBS] 요청 실패: {e}")

    soup = BeautifulSoup(res.text, "html.parser")

    selectors_to_try: List[str] = []
    if SELECTOR_HEADLINES:
        selectors_to_try.append(SELECTOR_HEADLINES)
    selectors_to_try.extend(DEFAULT_FALLBACK_SELECTORS)

    seen = set()
    headlines: List[str] = []
    for css in selectors_to_try:
        for a in soup.select(css):
            text = _clean_text(a.get_text(" ", strip=True))
            # 너무 짧은 텍스트/공백/중복 제거
            if len(text) < 5 or text in seen:
                continue
            # 메뉴/카테고리 등 비기사성 텍스트 필터링(느슨하게)
            if re.search(r"(KBS|메뉴|홈|검색|더보기|구독|로그인|인기|이벤트)$", text):
                continue
            seen.add(text)
            headlines.append(text)
            if len(headlines) >= limit:
                break
        if len(headlines) >= limit:
            break

    if not headlines:
        raise RuntimeError(
            "헤드라인을 찾지 못했습니다. 브라우저 DevTools로 실제 기사 제목 <a>의 셀렉터를 확인해 "
            "SELECTOR_HEADLINES 값을 지정해 보세요."
        )
    return headlines


# -----------------------------
# 2) 날씨 (Open‑Meteo Public API, 키 불필요)
# -----------------------------

def fetch_weather_seoul() -> List[str]:
    """서울 현재 날씨 요약을 리스트로 반환 (Open‑Meteo, 무료/공개 API)."""
    # 서울 좌표 (위도/경도)
    lat, lon = 37.5665, 126.9780
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m"
        "&timezone=Asia%2FSeoul"
    )
    try:
        res = requests.get(url, timeout=10, headers=HEADERS)
        res.raise_for_status()
        data = res.json().get("current", {})
    except Exception as e:
        raise SystemExit(f"[Weather] 요청 실패: {e}")

    out: List[str] = []
    def line(kor: str, key: str, suffix: str = "") -> None:
        v = data.get(key)
        if v is not None:
            out.append(f"{kor}: {v}{suffix}")

    line("기온(2m)", "temperature_2m", "°C")
    line("체감온도", "apparent_temperature", "°C")
    line("상대습도", "relative_humidity_2m", "%")
    line("풍속(10m)", "wind_speed_10m", " m/s")

    if not out:
        out.append("날씨 데이터를 가져오지 못했습니다.")
    return out


# -----------------------------
# 3) 주식 (Google Finance 페이지 파싱, BeautifulSoup + 정규식)
# -----------------------------

_PRICE_RE = re.compile(r"(?:₩|KRW)?\s?[\d,]+(?:\.\d+)?")

def fetch_stock_price(symbol: str = "005930:KRX") -> List[str]:
    """
    Google Finance에서 심볼의 현재 가격과 보조 정보를 간단 파싱.
    - symbol 예: '005930:KRX' (삼성전자), '035420:KRX' (NAVER)
    """
    g_url = f"https://www.google.com/finance/quote/{symbol}"
    try:
        res = requests.get(g_url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        raise SystemExit(f"[Stock] 요청 실패: {e}")

    soup = BeautifulSoup(res.text, "html.parser")

    text = soup.get_text(" ", strip=True)
    # 첫 번째 '₩xx,xxx' 형태를 우선 사용
    m = re.search(r"₩\s?[\d,]+(?:\.\d+)?", text)
    price = m.group(0) if m else None

    # 보조 정보: 전일 종가, 일중/52주 범위 등도 흔히 페이지에 텍스트로 포함됨
    prev_close = None
    day_range = None
    year_range = None

    # 간단한 키워드 주변에서 숫자 추출
    def find_after(keyword: str) -> Optional[str]:
        idx = text.find(keyword)
        if idx == -1:
            return None
        tail = text[idx : idx + 200]  # 키워드 뒤 200자에서만 검색
        mm = _PRICE_RE.findall(tail)
        return mm[0] if mm else None

    prev_close = find_after("Previous close") or find_after("이전 종가")
    # Day range, Year range는 범위 두 값이므로 2개 매치가 있으면 "a - b"로 구성
    def find_range(k: str) -> Optional[str]:
        idx = text.find(k)
        if idx == -1:
            return None
        tail = text[idx : idx + 120]
        mm = _PRICE_RE.findall(tail)
        if len(mm) >= 2:
            return f"{mm[0]} - {mm[1]}"
        return None

    day_range = find_range("Day range") or find_range("일중 범위")
    year_range = find_range("Year range") or find_range("52-week range") or find_range("연중 범위")

    lines = []
    lines.append(f"심볼: {symbol}")
    lines.append(f"현재가: {price or 'N/A'}")
    if prev_close:
        lines.append(f"전일 종가: {prev_close}")
    if day_range:
        lines.append(f"일중 범위: {day_range}")
    if year_range:
        lines.append(f"52주 범위: {year_range}")
    return lines


# -----------------------------
# 출력 유틸
# -----------------------------

def print_list(title: str, items: List[str]) -> None:
    print(f"\n[{title}] ({len(items)}개)\n" + "-" * 60)
    for i, v in enumerate(items, 1):
        print(f"{i:2d}. {v}")


# -----------------------------
# CLI
# -----------------------------

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="crawling_KBS.py",
        description="KBS 헤드라인/날씨/주식 정보를 간단히 수집해 출력합니다."
    )
    sub = p.add_subparsers(dest="command", required=True)

    # kbs
    pk = sub.add_parser("kbs", help="KBS 헤드라인 가져오기 (BeautifulSoup)")
    pk.add_argument("--limit", type=int, default=10, help="가져올 기사 수 (기본 10)")
    pk.add_argument("--url", type=str, default="https://news.kbs.co.kr", help="수집 대상 URL")

    # weather
    pw = sub.add_parser("weather", help="서울 현재 날씨(Open‑Meteo)")
    # 확장용: 좌표를 바꾸고 싶으면 아래 인자를 열어서 사용하세요.
    # pw.add_argument("--lat", type=float, default=37.5665)
    # pw.add_argument("--lon", type=float, default=126.9780)

    # stock
    ps = sub.add_parser("stock", help="주식 가격 (Google Finance 페이지 파싱)")
    ps.add_argument("--symbol", type=str, default="005930:KRX",
                    help="심볼(예: 005930:KRX, 035420:KRX 등)")

    args = p.parse_args(argv)

    try:
        if args.command == "kbs":
            headlines = fetch_kbs_headlines(limit=args.limit, url=args.url)
            print_list("KBS 주요 헤드라인", headlines)
        elif args.command == "weather":
            w = fetch_weather_seoul()
            print_list("서울 현재 날씨", w)
        elif args.command == "stock":
            s = fetch_stock_price(symbol=args.symbol)
            print_list("주식 시세", s)
        else:
            p.print_help()
            return 1
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
