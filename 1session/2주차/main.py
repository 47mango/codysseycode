import csv

file_path = 'D:/study/codysseycode/2주차/Mars_Base_Inventory_List.csv'

result_path = './2주차/Mars_Base_Inventory_danger.csv'

result_bin = './2주차/Mars_Base_Inventory_List.bin'

data = list()


try:
    # csv파일을 읽기모드 'r'로 열기(인코딩 'cp949')
    with open(file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file) # 파일 객체를 csv.reader의 인자로 전달해 새로운 reader 객체 생성
        for row in csv_reader: 
            print(row)
            data.append(row)

    # 마지막 5번째 항목만 float 변환 (예외 처리 추가)
    for row in data:
        try:
            row[-1] = float(row[-1])  # 숫자로 변환 가능한 경우 변환
        except ValueError:
            pass  # 변환 불가능하면 그대로 둠 ( 맨처음 줄이 문자열만 있기 때문에 )


    sorted_data = [data[0]] + sorted(
        data[1:], 
        # 인화성 수치가 높은 순으로 정렬 ( 처음에 문자열 있으니 문자열은 만나면 최상위 배치 )
        key=lambda x: float(x[-1]) if isinstance(x[-1], (int, float)) else float('-inf'), 
        reverse=True
    )

    print('---------------------------------------------')
    for row in sorted_data:
        print(row)


    # 인화성 수치가 0.7 이상 인것만 추출해서 넣는데 문자열을 만나면 무시
    danger_flam = list(filter(lambda x: x[-1] > 0.7 if isinstance(x[-1], (int, float)) else False, sorted_data))

    print('---------------------------------------------')
    for row in danger_flam:
        print(row)

    with open(result_path,'w', encoding='utf-8') as file:
        for row in danger_flam:
            file.write(",".join(map(str, row)) + "\n")


    #--------------------------------------- 추가 문제 부분 : 바이너리 파일로 데이터 저장 --------------------------------------------
    with open(result_bin, 'wb') as file:
        for row in danger_flam:
            line = ",".join(map(str, row)) + "\n"  # 리스트를 문자열로 변환
            file.write(line.encode("utf-8"))  # 문자열을 바이트로 변환 후 저장


    print('---------------------------------------------')
    with open(result_bin, 'rb') as file:
        for line in file:
            row = line.decode("utf-8").strip().split(",")  # 바이트 → 문자열 변환 후 리스트로 변환
            print(row)  # 즉시 출력

#파일 찾을수 없을때
except FileNotFoundError:
 print(f'파일을 찾을 수 없습니다. ')
# 권한 없을떄
except PermissionError:
 print(f'파일에 접근할 권한이 없습니다.')
#인코딩 문제
except UnicodeDecodeError:
 print(f'파일 인코딩 문제 발생. 다른 인코딩을 시도해 보세요. ')
#이외 오류
except Exception as e:
 print(f'오류 발생: {e}')