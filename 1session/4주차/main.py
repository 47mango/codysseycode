import time
import json
import random
import threading
from datetime import datetime

class DummySensor:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0.0,     # 화성 기지 내부 온도
            'mars_base_external_temperature': 0.0,     # 화성 기지 외부 온도
            'mars_base_internal_humidity': 0.0,        # 화성 기지 내부 습도
            'mars_base_external_illuminance': 0.0,     # 화성 기지 외부 광량
            'mars_base_internal_co2': 0.0,             # 화성 기지 내부 이산화탄소 농도
            'mars_base_internal_oxygen': 0.0           # 화성 기지 내부 산소 농도
        }

    def set_env(self):
        self.env_values['mars_base_internal_temperature'] = random.randint(18, 30)
        self.env_values['mars_base_external_temperature'] = random.randint(0, 21)
        self.env_values['mars_base_internal_humidity'] = random.randint(50, 60)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 2)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 4)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4.0, 7.0), 2)

    def get_env(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = (
            f"{now}, "
            f"{self.env_values['mars_base_internal_temperature']}°C, "
            f"{self.env_values['mars_base_external_temperature']}°C, "
            f"{self.env_values['mars_base_internal_humidity']}%, "
            f"{self.env_values['mars_base_external_illuminance']} W/m², "
            f"{self.env_values['mars_base_internal_co2']}%, "
            f"{self.env_values['mars_base_internal_oxygen']}%\n"
        )

        with open('./3주차/sensor_log.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(log_line)

        return self.env_values


class MissionComputer:
    def __init__(self):
        self.sensor = DummySensor()
        self.env_values = {}
        self.running = True
        self.data_log = []

    def get_sensor_data(self):
        start_time = time.time()

        while self.running:
            self.sensor.set_env()
            self.env_values = self.sensor.get_env()
            self.data_log.append(self.env_values)

            print(json.dumps(self.env_values, indent=2, ensure_ascii=False))

            # 5분마다 평균 계산 및 출력
            elapsed = time.time() - start_time
            if elapsed >= 300:  # 5분 = 300초
                self.print_average()
                self.data_log.clear()
                start_time = time.time()

            time.sleep(5)

        print("System stopped...")

    def print_average(self):
        if not self.data_log:
            return

        avg_values = {}
        keys = self.data_log[0].keys()

        for key in keys:
            total = sum(item[key] for item in self.data_log)
            avg = round(total / len(self.data_log), 4)
            avg_values[key] = avg

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[5분 평균 출력 - {now}]")
        print(json.dumps(avg_values, indent=2, ensure_ascii=False))

    def listen_for_stop(self):
        input("종료하려면 Enter 키를 누르세요...\n")
        self.running = False

    def run(self):
        sensor_thread = threading.Thread(target=self.get_sensor_data)
        stop_thread = threading.Thread(target=self.listen_for_stop)

        sensor_thread.start()
        stop_thread.start()

        sensor_thread.join()
        stop_thread.join()

# 실행
RunComputer = MissionComputer()
RunComputer.run()
