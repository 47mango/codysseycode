file_path = 'D:/study/codysseycode/1주차/mission_computer_main.log'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

        # for line in lines:
        #     print(line.strip())

        # 리스트를 거꾸로 뒤집어 출력
        for line in reversed(lines):  
            print(line.strip())

except FileNotFoundError:
    print(f"파일을 찾을 수 없습니다: {file_path}")
except Exception as e:
    print(f"오류 발생: {e}")
