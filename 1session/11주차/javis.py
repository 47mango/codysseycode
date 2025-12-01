#!/usr/bin/env python3
"""
javis.py

This script lists all recorded WAV audio files in the RECORDS_DIR directory,
performs Speech-to-Text (STT) on each file in fixed-duration chunks, and
saves the recognized text with timestamps to CSV files (one CSV per audio file).
Also provides a bonus function to search for a keyword within the saved CSVs.
"""

import os
import wave
import math
import csv
import sys

try:
    import speech_recognition as sr
except ImportError:
    print('ERROR: speech_recognition 모듈을 찾을 수 없습니다. '
          '먼저 "pip install SpeechRecognition"을 실행하세요.')
    sys.exit(1)

# 디렉토리 경로 설정 (음성 파일들이 저장된 위치)
RECORDS_DIR = 'records'
# STT를 처리할 때 사용할 청크(초 단위) 길이
CHUNK_DURATION = 5  # 초


def list_audio_files(directory):
    """
    주어진 디렉토리 내의 WAV 파일 목록을 반환합니다.

    :param directory: 음성 파일이 저장된 디렉토리 경로
    :return: WAV 파일 경로들의 리스트
    """
    files = []
    for filename in os.listdir(directory):
        if filename.lower().endswith('.wav'):
            files.append(os.path.join(directory, filename))
    return files


def get_audio_duration(file_path):
    """
    wave 모듈을 사용하여 WAV 파일의 총 길이를 초 단위로 계산합니다.

    :param file_path: WAV 파일 경로
    :return: 오디오 전체 길이(초)
    """
    with wave.open(file_path, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
    return duration


def transcribe_file(file_path, chunk_duration=CHUNK_DURATION):
    """
    주어진 WAV 파일을 일정한 길이(chunk_duration)로 나누어 STT를 수행하고,
    각 청크별 시작 시간을 기록하여 (timestamp, recognized_text) 쌍의 리스트를 반환합니다.

    :param file_path: WAV 파일 경로
    :param chunk_duration: 초 단위 청크 길이
    :return: 리스트 of (timestamp_str, recognized_text)
    """
    recognizer = sr.Recognizer()
    results = []

    total_duration = get_audio_duration(file_path)
    num_chunks = math.ceil(total_duration / chunk_duration)

    for i in range(num_chunks):
        start_time = i * chunk_duration
        # 각 청크를 읽어들여 STT 수행
        with sr.AudioFile(file_path) as source:
            try:
                audio_data = recognizer.record(source,
                                               offset=start_time,
                                               duration=chunk_duration)
            except Exception as e:
                print(f'ERROR: "{file_path}"의 {start_time}초~{start_time + chunk_duration}초 구간을 읽는 중 오류 발생: {e}')
                continue

        try:
            # recognize_google 사용, 필요시 language='ko-KR' 등을 지정 가능
            text = recognizer.recognize_google(audio_data, language='ko-KR')
        except sr.UnknownValueError:
            text = ''
        except sr.RequestError as e:
            print(f'ERROR: Google STT 요청 실패 ({e})')
            text = ''

        # 타임스탬프를 "HH:MM:SS" 형식으로 변환
        hours = int(start_time // 3600)
        minutes = int((start_time % 3600) // 60)
        seconds = int(start_time % 60)
        timestamp_str = f'{hours:02d}:{minutes:02d}:{seconds:02d}'

        results.append((timestamp_str, text))

    return results


def save_transcription_to_csv(file_path, transcripts):
    """
    음성 파일 이름과 동일한 이름의 CSV 파일에 STT 결과를 저장합니다.
    CSV 헤더: time, text

    :param file_path: WAV 파일 경로
    :param transcripts: (timestamp, text) 튜플의 리스트
    """
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    csv_filename = f'{base_name}.CSV'
    csv_path = os.path.join(os.path.dirname(file_path), csv_filename)

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['time', 'text'])
            for timestamp, text in transcripts:
                writer.writerow([timestamp, text])
    except Exception as e:
        print(f'ERROR: "{csv_path}"에 CSV를 쓰는 중 오류 발생: {e}')


def transcribe_all():
    """
    RECORDS_DIR 디렉토리 내의 모든 WAV 파일에 대해 STT를 수행하고
    결과를 CSV로 저장합니다.
    """
    if not os.path.isdir(RECORDS_DIR):
        print(f'ERROR: "{RECORDS_DIR}" 디렉토리를 찾을 수 없습니다.')
        return

    audio_files = list_audio_files(RECORDS_DIR)
    if not audio_files:
        print(f'경고: "{RECORDS_DIR}" 디렉토리에 WAV 파일이 없습니다.')
        return

    for idx, audio_path in enumerate(audio_files, start=1):
        print(f'[{idx}/{len(audio_files)}] "{audio_path}" 처리 중...')
        transcripts = transcribe_file(audio_path)
        save_transcription_to_csv(audio_path, transcripts)
        print(f'    -> "{os.path.splitext(os.path.basename(audio_path))[0]}.CSV" 저장 완료')


def search_keyword_in_csv(keyword):
    """
    저장된 CSV 파일들(같은 디렉토리, 확장자 .CSV)에서 특정 키워드를 검색하여
    일치하는 항목을 출력합니다.

    :param keyword: 검색할 문자열
    """
    if not os.path.isdir(RECORDS_DIR):
        print(f'ERROR: "{RECORDS_DIR}" 디렉토리를 찾을 수 없습니다.')
        return

    csv_files = [f for f in os.listdir(RECORDS_DIR) if f.upper().endswith('.CSV')]
    if not csv_files:
        print(f'경고: "{RECORDS_DIR}" 디렉토리에 CSV 파일이 없습니다.')
        return

    found_any = False
    for csv_filename in csv_files:
        csv_path = os.path.join(RECORDS_DIR, csv_filename)
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)  # 헤더 건너뛰기
                for row in reader:
                    if len(row) < 2:
                        continue
                    timestamp, text = row[0], row[1]
                    if keyword in text:
                        if not found_any:
                            print(f'\n=== "{keyword}" 검색 결과 ===')
                        print(f'파일: {csv_filename} | 시간: {timestamp} | 내용: {text}')
                        found_any = True
        except Exception as e:
            print(f'ERROR: "{csv_path}"을(를) 읽는 중 오류 발생: {e}')

    if not found_any:
        print(f'키워드 "{keyword}"에 대한 결과를 찾을 수 없습니다.')


def print_usage():
    """
    스크립트 사용법 안내를 출력합니다.
    """
    print('사용법:')
    print('  python javis.py transcribe    # 모든 WAV 파일을 STT 처리하여 CSV로 저장')
    print('  python javis.py search <키워드>  # 저장된 CSV 파일들에서 <키워드> 검색')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1].lower()
    if command == 'transcribe':
        transcribe_all()
    elif command == 'search':
        if len(sys.argv) < 3:
            print('ERROR: 검색할 키워드를 입력하세요.')
            print_usage()
        else:
            keyword = sys.argv[2]
            search_keyword_in_csv(keyword)
    else:
        print(f'ERROR: 알 수 없는 명령 "{command}"')
        print_usage()
