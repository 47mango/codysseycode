# door_hacking.py

import zipfile                    # zip 파일을 다루기 위한 표준 라이브러리
import itertools                  # 가능한 모든 조합을 생성하는 데 사용
import string                     # 알파벳, 숫자 등의 문자 집합 제공
import time                       # 시간 측정용
from multiprocessing import Pool, cpu_count  # 병렬 처리를 위한 멀티프로세싱 모듈

# zip 파일 경로를 전역 변수로 정의 (worker 프로세스에서 접근 가능하도록)
zip_file_name = "D:/study/codysseycode/8주차/emergency_storage_key.zip"

# 실제로 비밀번호를 시도해보는 함수 (멀티프로세싱 대상)
def try_password(password: str) -> str | None:
    try:
        # zip 파일을 열고 비밀번호로 압축 해제 시도
        with zipfile.ZipFile(zip_file_name) as zip_file:
            zip_file.extractall(pwd=password.encode())  # password는 문자열 → bytes로 변환
        return password  # 성공한 비밀번호를 반환
    except:
        return None  # 실패 시 None 반환

# 병렬로 암호를 시도하는 메인 함수
def unlock_zip_parallel():
    charset = string.ascii_lowercase + string.digits  # 소문자 + 숫자로 구성된 비밀번호 후보
    max_length = 6  # 최대 비밀번호 길이 (6자리)

    start_time = time.time()  # 시작 시간 기록
    print("암호 해제를 시작합니다...")

    # CPU 코어 수만큼 프로세스를 만들어 풀을 구성
    with Pool(cpu_count()) as pool:
        # itertools.product로 가능한 모든 조합 생성 → ''.join으로 문자열로 변환
        combinations = map(''.join, itertools.product(charset, repeat=max_length))

        # 병렬로 password 시도 실행 (imap_unordered는 순서를 보장하지 않음 → 더 빠름)
        for i, result in enumerate(pool.imap_unordered(try_password, combinations)):
            if result:
                duration = time.time() - start_time  # 성공 시 걸린 시간 측정
                print(f"성공! 암호는 '{result}'입니다.")
                print(f"총 시도 횟수: {i + 1}")
                print(f"총 소요 시간: {duration:.2f}초")

                # 성공한 암호를 파일로 저장
                with open("password.txt", "w") as f:
                    f.write(result)

                pool.terminate()  # 더 이상 작업할 필요 없으므로 중단
                return

            # 진행 상황을 주기적으로 출력 (1만 회마다)
            if i % 10000 == 0:
                elapsed = time.time() - start_time
                print(f"{i}회 시도 중... 경과 시간: {elapsed:.2f}초")

    print("암호를 찾지 못했습니다.")  # 전체 탐색에도 실패한 경우

# 엔트리 포인트: 직접 실행될 때만 작동
if __name__ == "__main__":
    unlock_zip_parallel()
