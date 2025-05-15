# door_hacking.py
import zipfile
import itertools
import string
import time

def unlock_zip():
    zip_file_name = "D:/study/codysseycode/8주차/emergency_storage_key.zip"
    charset = string.ascii_lowercase + string.digits  # 소문자 + 숫자
    max_length = 6

    try:
        zip_file = zipfile.ZipFile(zip_file_name)
    except FileNotFoundError:
        print("오류: ZIP 파일이 존재하지 않습니다.")
        return
    except zipfile.BadZipFile:
        print("오류: 잘못된 ZIP 파일입니다.")
        return

    start_time = time.time()
    attempt = 0

    print("암호 해제를 시작합니다...")
    for candidate in itertools.product(charset, repeat=max_length):
        password = ''.join(candidate)
        attempt += 1

        try:
            zip_file.extractall(pwd=password.encode())
            end_time = time.time()
            duration = end_time - start_time
            print(f"성공! 암호는 '{password}'입니다.")
            print(f"총 시도 횟수: {attempt}")
            print(f"총 소요 시간: {duration:.2f}초")

            with open("password.txt", "w") as f:
                f.write(password)
            return
        except RuntimeError:
            # 잘못된 암호일 경우
            if attempt % 10000 == 0:
                elapsed = time.time() - start_time
                print(f"{attempt}회 시도 중... 경과 시간: {elapsed:.2f}초")
            continue
        except Exception as e:
            print(f"예외 발생: {e}")
            continue

    print("암호를 찾지 못했습니다.")

if __name__ == "__main__":
    unlock_zip()
