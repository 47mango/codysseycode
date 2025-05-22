#!/usr/bin/env python3
# caesar_decode.py

import string
import sys

def caesar_cipher_decode(target_text: str):
    """
    주어진 문자열에 대해 0부터 25까지 모든 시프트 값으로
    카이사르 암호를 해독하고 결과를 리스트로 반환합니다.
    """
    def shift_char(c: str, shift: int) -> str:
        if 'a' <= c <= 'z':
            return chr((ord(c) - ord('a') - shift) % 26 + ord('a'))
        elif 'A' <= c <= 'Z':
            return chr((ord(c) - ord('A') - shift) % 26 + ord('A'))
        else:
            return c  # 영문자 외 문자는 그대로 반환

    decoded_results = []
    print("----- 카이사르 암호 해독 시도 (0~25) -----")
    for shift in range(26):
        decoded = ''.join(shift_char(c, shift) for c in target_text)
        decoded_results.append(decoded)
        print(f"[{shift:2d}] {decoded}")

    return decoded_results

def main():
    # 1) password.txt 파일에서 암호문 읽어오기
    try:
        with open("password.txt", "r", encoding="utf-8") as f:
            encrypted_text = f.read().strip()
    except FileNotFoundError:
        print("Error: 'password.txt' 파일을 찾을 수 없습니다.")
        sys.exit(1)

    # 2) 모든 시프트 값에 대해 해독 시도 및 출력
    all_options = caesar_cipher_decode(encrypted_text)

    # 3) 사용자에게 올바른 시프트 번호 입력받기
    try:
        choice = int(input("\n정상적으로 읽히는 해독 결과의 번호를 입력하세요 (0~25): ").strip())
        if not 0 <= choice < 26:
            raise ValueError
    except ValueError:
        print("Error: 0에서 25 사이의 정수만 입력 가능합니다.")
        sys.exit(1)

    # 4) 선택된 해독 결과를 result.txt에 저장
    result = all_options[choice]
    try:
        with open("result.txt", "w", encoding="utf-8") as out:
            out.write(result)
        print(f"성공: 해독 결과[{choice}]를 'result.txt'에 저장했습니다.")
    except IOError as e:
        print(f"Error: 'result.txt'에 쓰는 도중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
