#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawling_KBS.py
================
학습용 KBS 헤드라인/날씨/주식 크롤러 (BeautifulSoup)

요구사항 체크리스트
- [x] KBS http://news.kbs.co.kr 접속 후 주요 헤드라인 뉴스 확인
- [x] BeautifulSoup 설치 안내 (아래 사용법 참고)
- [x] 개발자 도구로 찾은 "고유한 값"(CSS 선택자)로 헤드라인 추출
- [x] BeautifulSoup 주요 기능으로 파싱(find, select, get_text 등)
- [x] 헤드라인을 List 객체에 저장 후 화면에 출력
- [x] 최종 소스를 crawling_KBS.py로 저장
- [x] KBS 외 날씨/주식 가격 등 다른 사이트 크롤링 예시 포함

사용 전 설치 (최초 1회):
    pip install requests beautifulsoup4 lxml

실행 예시:
    # KBS 헤드라인 출력
    python crawling_KBS.py kbs
    # KBS 헤드라인 출력 + 파일 저장
    python crawling_KBS.py kbs --save kbs_headlines.txt

    # 주식 가격 (Yahoo Finance)
    python crawling_KBS.py stock AAPL
    python crawling_KBS.py stock 005930.KS   # 삼성전자

    # 날씨 (기상청 RSS, 서울 종로구 zone 기본값=1111000000)
    python crawling_KBS.py weather --zone 1111000000 --limit 6

개발자 도구로 "고유한 값" 찾기 팁:
1) 크롬에서 https://news.kbs.co.kr/ 열기 → 개발자 도구 (F12)
2) 마우스로 메인 헤드라인 제목 링크에 호버 → 해당 <a> 엘리먼트 확인
3) 자주 보이는 패턴 예:
   - 기사 상세 링크: a[href^="/news/view.do?"]
   - 절대경로: a[href^="https://news.kbs.co.kr/news/view.do?"]
   - 상단 블록: div.headline a, 또는 h2/h3/h4 아래의 a
4) 위와 같은 CSS 선택자를 BeautifulSoup의 soup.select(...) 로 사용

주의: 실제 사이트 구조는 수시로 변경될 수 있습니다. 본 코드는 연습 목적이며,
     실패 시 RSS(https://news.kbs.co.kr/rss/news_main.htm)로 폴백합니다.
     각 사이트의 robots.txt, 이용약관을 준수하세요.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# 공용 유틸
# ---------------------------------------------------------------------------
def fetch(url: str, timeout: int = 15) -> Optional[requests.Response]:
    """간단한 GET 래퍼. 실패 시 None 반환."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp
    except Exception as e:
        print(f"[fetch] 요청 실패: {url} -> {e}", file=sys.stderr)
        return None

def pretty_print_list(items: List[str], title: str = "결과") -> None:
    """리스트를 번호와 함께 보기 좋게 출력."""
    print(f"\n[{title} | 총 {len(items)}개]")
    print("-" * 80)
    for i, s in enumerate(items, 1):
        print(f"{i}. {s}")

# ---------------------------------------------------------------------------
# 1) KBS 헤드라인
# ---------------------------------------------------------------------------
def parse_kbs_headlines_from_html(html: str) -> List[Tuple[str, str]]:
    """
    KBS 메인 페이지 HTML에서 (제목, 링크) 튜플 리스트 추출.
    BeautifulSoup 주요 기능 사용:
      - soup.select, soup.find_all
      - a.get_text(), a.get("href")
    여러 CSS 선택자를 시도해 구조 변경에 유연하게 대응합니다.
    """
    soup = BeautifulSoup(html, "lxml")
    results: List[Tuple[str, str]] = []
    seen = set()

    selectors = [
        'a[href^="/news/view.do?"]',
        'a[href^="https://news.kbs.co.kr/news/view.do?"]',
        'div.headline a',
        'h2 a', 'h3 a', 'h4 a',
    ]

    for sel in selectors:
        for a in soup.select(sel):
            title = (a.get_text() or "").strip()
            href = (a.get("href") or "").strip()
            if not title or not href:
                continue
            if len(title) < 6:  # 너무 짧은 제목 제거
                continue
            if href.startswith("/"):
                href = "https://news.kbs.co.kr" + href
            key = (title, href)
            if key in seen:
                continue
            seen.add(key)
            results.append(key)

    # 상위 20개 정도만
    return results[:20]

def parse_kbs_headlines_from_rss(xml: str) -> List[Tuple[str, str]]:
    """RSS에서 (제목, 링크) 튜플 리스트 추출."""
    soup = BeautifulSoup(xml, "xml")
    items = soup.find_all("item")
    results: List[Tuple[str, str]] = []
    for it in items:
        title = (it.title.get_text() if it.title else "").strip()
        link = (it.link.get_text() if it.link else "").strip()
        if title and link:
            results.append((title, link))
    return results[:20]

def get_kbs_headlines() -> List[Tuple[str, str]]:
    """우선 HTML 파싱, 실패 시 RSS 폴백."""
    print("[KBS] 메인 페이지에서 헤드라인 수집 시도...")
    r = fetch("https://news.kbs.co.kr/")
    if r and r.text:
        items = parse_kbs_headlines_from_html(r.text)
        if items:
            return items
        print("[KBS] HTML 파싱 결과 없음. RSS로 폴백합니다.", file=sys.stderr)

    print("[KBS] RSS 수집 시도...")
    rr = fetch("https://news.kbs.co.kr/rss/news_main.htm")
    if rr and rr.text:
        return parse_kbs_headlines_from_rss(rr.text)

    print("[KBS] 헤드라인 수집 실패", file=sys.stderr)
    return []

def cmd_kbs(args: argparse.Namespace) -> None:
    items = get_kbs_headlines()

    # List 객체로 보관 (문자열로 변환하여 보기 좋게)
    headline_list: List[str] = [
        f"{title} ({link})" for title, link in items
    ]

    # 화면 출력
    pretty_print_list(headline_list, title="KBS 헤드라인")

    # 저장 옵션
    if args.save:
        try:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write("\n".join(headline_list))
            print(f"\n[KBS] 결과를 '{args.save}' 파일로 저장했습니다.")
        except Exception as e:
            print(f"[KBS] 저장 실패: {e}", file=sys.stderr)

# ---------------------------------------------------------------------------
# 2) 주식 가격 (Yahoo Finance) 예시
# ---------------------------------------------------------------------------
def get_stock_price_yahoo(ticker: str) -> Optional[str]:
    """
    Yahoo Finance 상세 페이지에서 현재가를 파싱.
    - BeautifulSoup select로 fin-streamer[data-field="regularMarketPrice"] 추출
    - 예: AAPL, MSFT, 005930.KS
    """
    url = f"https://finance.yahoo.com/quote/{ticker}"
    r = fetch(url)
    if not r or not r.text:
        return None

    soup = BeautifulSoup(r.text, "lxml")
    node = soup.select_one('fin-streamer[data-field="regularMarketPrice"]')
    if node and node.get_text(strip=True):
        return node.get_text(strip=True)

    # 백업 셀렉터
    alt = soup.select_one('fin-streamer[data-test="qsp-price"]')
    if alt and alt.get_text(strip=True):
        return alt.get_text(strip=True)

    return None

def cmd_stock(args: argparse.Namespace) -> None:
    price = get_stock_price_yahoo(args.ticker)
    if price is None:
        print(f"[STOCK] '{args.ticker}' 가격을 가져오지 못했습니다.", file=sys.stderr)
        return
    pretty_print_list([f"{args.ticker}: {price}"], title="주식 현재가")

# ---------------------------------------------------------------------------
# 3) 날씨 (기상청 RSS) 예시
# ---------------------------------------------------------------------------
def get_weather_kma_rss(zone_code: str = "1111000000", limit: int = 6) -> List[str]:
    """
    기상청 1시간 단기예보 RSS 파싱.
    참고 URL 형식(변경 가능성 있음):
      https://www.weather.go.kr/w/rss/dfs/hr1-forecast.do?zone=1111000000
    BeautifulSoup의 XML 파서 사용.
    """
    url = f"https://www.weather.go.kr/w/rss/dfs/hr1-forecast.do?zone={zone_code}"
    r = fetch(url)
    if not r or not r.text:
        return []

    soup = BeautifulSoup(r.text, "xml")
    items = soup.find_all("data")
    out: List[str] = []
    for i, it in enumerate(items):
        if i >= limit:
            break
        hour = it.find_text("hour") or "?"
        temp = it.find_text("temp") or "?"
        wf   = it.find_text("wfKor") or it.find_text("wfEn") or "?"
        pop  = it.find_text("pop") or "?"
        reh  = it.find_text("reh") or "?"
        out.append(f"{hour}시 | {wf} | 기온 {temp}°C | 강수확률 {pop}% | 습도 {reh}%")
    return out

def cmd_weather(args: argparse.Namespace) -> None:
    lines = get_weather_kma_rss(args.zone, args.limit)
    if not lines:
        print("[WEATHER] 날씨 정보를 가져오지 못했습니다.", file=sys.stderr)
        return
    pretty_print_list(lines, title=f"기상청({args.zone}) {len(lines)}시간 예보")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="KBS 헤드라인/주식/날씨 크롤러 (BeautifulSoup, 학습용)")
    sub = p.add_subparsers(dest="command", required=True)

    # kbs
    p_kbs = sub.add_parser("kbs", help="KBS 주요 헤드라인 수집")
    p_kbs.add_argument("--save", help="결과를 텍스트 파일로 저장 (예: kbs_headlines.txt)")
    p_kbs.set_defaults(func=cmd_kbs)

    # stock
    p_stock = sub.add_parser("stock", help="Yahoo Finance에서 주식 현재가 수집")
    p_stock.add_argument("ticker", help="종목 티커 (예: AAPL, MSFT, 005930.KS 등)")
    p_stock.set_defaults(func=cmd_stock)

    # weather
    p_weather = sub.add_parser("weather", help="기상청 1시간 단기예보 RSS")
    p_weather.add_argument("--zone", default="1111000000", help="행정구역 코드 (기본: 서울 종로구)")
    p_weather.add_argument("--limit", type=int, default=6, help="가져올 시간 수 (기본: 6)")
    p_weather.set_defaults(func=cmd_weather)

    return p

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
