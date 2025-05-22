#!/usr/bin/env python3
# caesar_decode.py

import sys
import string

def caesar_cipher_decode(target_text: str):
    """
    주어진 문자열(target_text)에 대해 0~25까지 모든 시프트 값으로
    카이사르 암호를 해독하고, 각 결과를 출력한 뒤 리스트로 반환합니다.
    """
    def shift_char(c: str, shift: int) -> str:
        if 'a' <= c <= 'z':
            # 소문자
            return chr((ord(c) - ord('a') - shift) % 26 + ord('a'))
        elif 'A' <= c <= 'Z':
            # 대문자
            return chr((ord(c) - ord('A') - shift) % 26 + ord('A'))
        else:
            # 알파벳이 아니면 그대로
            return c

    results = []
    print("----- 카이사르 암호 해독 시도 (0~25) -----")
    for shift in range(26):
        decoded = ''.join(shift_char(c, shift) for c in target_text)
        results.append(decoded)
        print(f"[{shift:2d}] {decoded}")
    return results

def main():
    # 1) password.txt 읽기
    try:
        with open("D:/study/codysseycode/9주차/password.txt", "r", encoding="utf-8") as f:
            encrypted = f.read().strip()
    except FileNotFoundError:
        print("Error: 'password.txt' 파일을 찾을 수 없습니다.")
        sys.exit(1)

    # 2) 모든 시프트 해독 및 출력
    options = caesar_cipher_decode(encrypted)

    # 3) 사용자로부터 올바른 시프트 번호 입력받기
    try:
        choice = int(input("\n올바르게 해독된 번호를 입력하세요 (0~25): ").strip())
        if not (0 <= choice < 26):
            raise ValueError
    except ValueError:
        print("Error: 0~25 사이의 정수만 입력 가능합니다.")
        sys.exit(1)

    # 4) 선택된 해독 결과를 result.txt에 저장
    result_text = options[choice]
    try:
        with open("/result.txt", "w", encoding="utf-8") as out:
            out.write(result_text)
        print(f"성공: 해독 결과 [{choice}] 를 'result.txt'에 저장했습니다.")
    except IOError as e:
        print(f"Error: 'result.txt' 저장 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

