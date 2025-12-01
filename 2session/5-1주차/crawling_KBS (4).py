#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawling_KBS.py

요구사항 요약
1) 네이버(https://www.naver.com)에 접속해 로그인 전/후 콘텐츠 차이를 파악하고,
   '로그인한 경우에만 보이는 콘텐츠'로 '네이버 메일 받은메일함의 제목들'을 선정해 크롤링합니다.
2) 셀레니움(Selenium) + webdriver-manager 로크롬드라이버를 자동 설치/실행합니다.
3) 로그인은 계정 ID/PW를 입력 방식으로 진행하며(2차 인증/캡차가 나오면 수동으로 완료 후 계속),
   로그인 후 https://mail.naver.com 에서 최근 메일 제목들을 가져옵니다.
4) 가져온 제목들은 파이썬 리스트로 담아 출력합니다.

⚠️ 주의/면책
- 자동화/스크래핑은 서비스 약관/로봇 정책을 위반할 수 있습니다. 본 코드는 교육용 예시이며,
  사용 전 반드시 네이버 약관/정책을 확인하고 본인 계정/목적으로만 사용하세요.
- 네이버 UI/셀렉터는 수시로 변경될 수 있어, 아래 SELECTORS를 필요 시 수정하세요.
- 2단계 인증/보안문자는 자동화가 어려워서 수동으로 통과해야 할 수 있습니다.

설치
    python -m pip install --upgrade pip
    python -m pip install selenium webdriver-manager

실행
    # 환경변수 방식 (권장)
    export NAVER_ID="your_id"
    export NAVER_PW="your_password"
    python crawling_KBS.py --max 30

    # 혹은 CLI 인자 방식
    python crawling_KBS.py --id your_id --pw your_password --max 30

옵션
    --max N            : 최대 몇 개의 메일 제목을 수집할지 (기본 20)
    --headless         : 브라우저 창을 띄우지 않고 실행 (2차인증 시 권장하지 않음)
    --pause-after-login: 로그인 버튼 클릭 후 일시정지하여 수동 인증을 완료하도록 함
"""

from __future__ import annotations

import os
import sys
import time
import argparse
from typing import List, Optional
import time, random
from selenium.webdriver.common.keys import Keys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

USER_ID = 'do_hh'
USER_PW = 'kimdohyun@1'

NAVER_HOME = "https://www.naver.com/"
NAVER_LOGIN = "https://nid.naver.com/nidlogin.login"
NAVER_MAIL = "https://mail.naver.com/"

# 메일 제목 후보 셀렉터(변경될 수 있으므로 필요 시 업데이트)
MAIL_SUBJECT_SELECTORS = [
    "strong.mail_title",            # 모바일/일부 버전
    "span.mail_title",
    "a.mail_title",
    "span.subject",                 # 데스크톱 신버전 대응 시도
    "strong.subject",
    "div.subject",
    "a.subject",
    "li div .subject",
]

def build_driver(headless: bool = False) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    # 안정성 옵션
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,900")
    # 한국어 페이지 선호
    opts.add_argument("--lang=ko-KR")
    # 드라이버 자동 설치/버전 매칭
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(2)
    return driver

def wait_for(driver: webdriver.Chrome, by: By, selector: str, timeout: int = 15):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))

def safe_get(driver: webdriver.Chrome, url: str, timeout: int = 60):
    driver.set_page_load_timeout(timeout)
    driver.get(url)

def smart_clear(el, is_mac=True):
    """입력창을 안전하게 초기화 (전체선택+삭제)"""
    el.click()
    if is_mac:
        el.send_keys(Keys.COMMAND, 'a')
    else:
        el.send_keys(Keys.CONTROL, 'a')
    el.send_keys(Keys.DELETE)
    time.sleep(0.15)

def human_type(el, text, min_s=0.07, max_s=0.18, punc_pause=(0.25, 0.5)):
    """문자를 하나씩 보내며 랜덤 간격으로 '사람처럼' 타이핑"""
    for ch in text:
        el.send_keys(ch)
        if ch in ",.?!:;":
            time.sleep(random.uniform(*punc_pause))
        else:
            time.sleep(random.uniform(min_s, max_s))    

def is_logged_in(driver: webdriver.Chrome) -> bool:
    """네이버 홈에서 로그인 상태를 추정."""
    try:
        safe_get(driver, NAVER_HOME, timeout=30)
        # 로그인 전에는 상단에 '로그인' 링크가 보일 가능성이 높음.
        # (UI가 바뀔 수 있어 부정확할 수 있음)
        login_candidates = driver.find_elements(By.PARTIAL_LINK_TEXT, "로그인")
        if login_candidates:
            return False
        # 또는 사용자 메뉴/메일 링크 존재로 판단
        mail_link = driver.find_elements(By.PARTIAL_LINK_TEXT, "메일")
        return len(mail_link) > 0
    except Exception:
        return False

def do_login(driver: webdriver.Chrome, user_id: str, user_pw: str, pause_after_login: bool = False) -> None:
    safe_get(driver, NAVER_LOGIN, timeout=60)
    # ID/PW 입력
    # 일반적으로 input#id, input#pw를 사용하지만 UI가 바뀔 수 있음
    id_box = None
    pw_box = None

    # 후보 셀렉터 시도
    for css in ["input#id", "input[name='id']"]:
        els = driver.find_elements(By.CSS_SELECTOR, css)
        if els:
            id_box = els[0]
            break

    for css in ["input#pw", "input[name='pw']"]:
        els = driver.find_elements(By.CSS_SELECTOR, css)
        if els:
            pw_box = els[0]
            break

    if not id_box or not pw_box:
        raise RuntimeError("로그인 입력창을 찾을 수 없습니다. 셀렉터를 업데이트 하세요.")

    # ID
    smart_clear(id_box, is_mac=True)
    human_type(id_box, user_id)          # ← 사람처럼 타이핑

    # PW
    smart_clear(pw_box, is_mac=True)
    human_type(pw_box, user_pw)          # ← 사람처럼 타이핑

    time.sleep(2)  # 서버 반응/렌더링 여유

    # 로그인 버튼 클릭
    # 과거: #log.login 또는 button[type='submit']
    login_btn = None
    for css in ["#log\\.login", "button[type='submit']", "button[data-nclick='login']"]:
        els = driver.find_elements(By.CSS_SELECTOR, css)
        if els:
            login_btn = els[0]
            break
    
    if not login_btn:
        # 엔터 전송으로 대체
        pw_box.submit()
    else:
        login_btn.click()

    # 수동 인증이 필요한 경우 사용자가 직접 처리할 수 있도록 대기 옵션
    if pause_after_login:
        print("[안내] 추가 인증(2차 인증/캡차 등)이 있다면 지금 완료하세요. 완료 후 엔터를 누르면 계속합니다.")
        try:
            input()
        except EOFError:
            pass

    # 로그인 성공 추정: 네이버 홈 재접속 후 '로그인' 링크 부재 확인
    try:
        WebDriverWait(driver, 30).until(lambda d: is_logged_in(d) is True)
    except TimeoutException:
        # 실패 가능성 -> 그래도 메일로 바로 진입 시도
        pass

def collect_public_home_samples(driver: webdriver.Chrome, max_items: int = 5) -> List[str]:
    """비로그인 상태에서 네이버 홈의 공개 영역 일부(예: 메인 뉴스 타이틀)를 샘플로 수집."""
    samples: List[str] = []
    try:
        safe_get(driver, NAVER_HOME, timeout=30)
        # 뉴스/트렌드 등 예상 타이틀 후보를 다각도로 시도
        title_selectors = [
            "a.media_end_head_headline",   # 뉴스 상세 (홈에선 안 잡힐 수 있음)
            "a.cluster_text_headline",     # 뉴스 클러스터
            "a.common_list_title",         # 일반 리스트형
            "strong.title",                # 일반 타이틀
            "a.theme_item .title",         # 테마형
            "a[href*='news']",
        ]
        seen = set()
        for sel in title_selectors:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in els:
                text = (el.text or "").strip()
                if len(text) >= 6 and text not in seen:
                    samples.append(text)
                    seen.add(text)
                    if len(samples) >= max_items:
                        return samples
    except Exception:
        pass
    return samples

def fetch_mail_subjects(driver: webdriver.Chrome, max_items: int = 20) -> List[str]:
    """로그인 된 세션으로 네이버 메일 받은메일함 제목들을 수집."""
    subjects: List[str] = []

    # 메일(데스크톱/모바일) 모두 시도 -> 모바일 UI가 프레임이 적어 비교적 단순
    for url in [NAVER_MAIL, "https://m.mail.naver.com/"]:
        try:
            safe_get(driver, url, timeout=60)
        except Exception:
            continue

        # 프레임 전환이 필요한 경우를 대비 (구버전)
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            # 메일 관련 프레임 추정
            for f in iframes:
                src = f.get_attribute("src") or ""
                title = f.get_attribute("title") or ""
                if "mail" in src or "mail" in title.lower():
                    driver.switch_to.frame(f)
                    break
        except Exception:
            pass

        # 다양한 셀렉터 시도
        for sel in MAIL_SUBJECT_SELECTORS:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    t = (el.text or "").strip()
                    # 모바일 UI의 경우 제목이 a > strong.mail_title 구조일 수 있음
                    if t and t not in subjects:
                        subjects.append(t)
                        if len(subjects) >= max_items:
                            return subjects
            except Exception:
                continue

        # 프레임 되돌리기
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        if subjects:
            break

    return subjects[:max_items]

def main():
    parser = argparse.ArgumentParser(description="Selenium으로 네이버 로그인 후 메일 제목 크롤링")
    parser.add_argument("--id", dest="user_id", type=str, default=USER_ID,
                        help="네이버 ID (기본: 코드 내 USER_ID)")
    parser.add_argument("--pw", dest="user_pw", type=str, default=USER_PW,
                        help="네이버 PW (기본: 코드 내 USER_PW)")
    parser.add_argument("--max", dest="max_items", type=int, default=20, help="가져올 메일 제목 최대 개수")
    parser.add_argument("--headless", action="store_true", help="브라우저 창을 띄우지 않고 실행")
    parser.add_argument("--pause-after-login", action="store_true", help="로그인 후 일시정지(2차인증 수동 처리용)")
    args = parser.parse_args()


    if not args.user_id or not args.user_pw:
        print("오류: ID/PW가 필요합니다. --id와 --pw 인자 또는 NAVER_ID/NAVER_PW 환경변수를 설정하세요.", file=sys.stderr)
        sys.exit(1)

    driver = build_driver(headless=args.headless)

    try:
        # 1) 비로그인 상태의 공개 콘텐츠 샘플 수집
        public_samples = collect_public_home_samples(driver, max_items=5)
        print("\n[비로그인 공개 콘텐츠 샘플]")
        for i, t in enumerate(public_samples, 1):
            print(f"{i:02d}. {t}")

        # 2) 로그인
        print("\n[로그인 진행]")
        do_login(driver, args.user_id, args.user_pw, pause_after_login=args.pause_after_login)

        # 3) 로그인 후 콘텐츠(메일 제목) 수집
        print("\n[로그인 후 전용 콘텐츠: 네이버 메일 받은메일함 제목 목록]")
        subjects = fetch_mail_subjects(driver, max_items=args.max_items)
        if not subjects:
            print("메일 제목을 찾지 못했습니다. 셀렉터를 업데이트하거나 모바일 메일(m.mail.naver.com)도 시도해 보세요.")
        else:
            # 요구사항: 리스트 객체에 담아두고 화면에 출력
            print(f"총 {len(subjects)}개 수집:")
            print(subjects)  # 리스트 자체를 출력
            # 보기 좋게 줄바꿈도 함께 출력
            for i, s in enumerate(subjects, 1):
                print(f"{i:02d}. {s}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
