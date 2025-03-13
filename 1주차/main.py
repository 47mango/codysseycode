print('Hello Mars')

#파일 경로
file_path = 'D:/study/codysseycode/1주차/mission_computer_main.log'


try:
 # 파일열어서 한줄씩 읽기
 with open(file_path, 'r', encoding='utf-8') as f:
  lines = f.readlines()

  # 리스트 정상 출력
  # for line in lines:
  #     print(line.strip())

  # 리스트를 거꾸로 뒤집어 출력
  for line in reversed(lines):  
   print(line.strip())

#파일 찾을수 없을때
except FileNotFoundError:
 print(f"파일을 찾을 수 없습니다: {file_path}")
# 권한 없을떄
except PermissionError:
 print(f"파일에 접근할 권한이 없습니다: {file_path}")
#인코딩 문제
except UnicodeDecodeError:
 print(f"파일 인코딩 문제 발생. 다른 인코딩을 시도해 보세요: {file_path}")
#이외 오류
except Exception as e:
 print(f"오류 발생: {e}")
