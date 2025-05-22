import zipfile
import itertools
import string
import time
import os

def unlock_zip():
    zip_file_path = "emergency_storage_key.zip"
    charset = string.ascii_lowercase + string.digits  # 'abcdefghijklmnopqrstuvwxyz0123456789'
    max_length = 6

    try:
        zip_file = zipfile.ZipFile(zip_file_path)
    except FileNotFoundError:
        print("❌ ZIP 파일이 존재하지 않습니다.")
        return
    except zipfile.BadZipFile:
        print("❌ 잘못된 ZIP 파일입니다.")
        return

    print("🔓 암호 해제를 시작합니다...")
    start_time = time.time()
    attempt = 0

    # 문자열 생성 순서 조정 (알파벳 먼저 시도)
    priority_charset = string.ascii_lowercase + string.digits

    for candidate in itertools.product(priority_charset, repeat=max_length):
        password = ''.join(candidate)
        attempt += 1

        try:
            zip_file.extractall(pwd=password.encode())
            elapsed = time.time() - start_time
            print(f"\n✅ 성공! 암호는 '{password}' 입니다.")
            print(f"🔁 총 시도 횟수: {attempt}")
            print(f"⏱️ 총 소요 시간: {elapsed:.2f}초")

            # 암호를 파일에 저장
            try:
                with open("password.txt", "w") as f:
                    f.write(password)
            except Exception:
                pass  # 파일 저장 오류 무시

            return  # 성공하면 종료

        except RuntimeError:
            if attempt % 10000 == 0:
                print(f"🔁 시도 횟수: {attempt}, 경과 시간: {time.time() - start_time:.2f}초, 현재: {password}")
        except Exception:
            continue  # 기타 예외 무시

    print("❌ 암호를 찾지 못했습니다.")

# 직접 실행할 수 있게 메인 가드 추가
if __name__ == "__main__":
    unlock_zip()
