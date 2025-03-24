
import random

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
        # 로그 포맷
        log_line = (
            f"{self.env_values['mars_base_internal_temperature']}°C, "
            f"{self.env_values['mars_base_external_temperature']}°C, "
            f"{self.env_values['mars_base_internal_humidity']}%, "
            f"{self.env_values['mars_base_external_illuminance']} W/m², "
            f"{self.env_values['mars_base_internal_co2']}%, "
            f"{self.env_values['mars_base_internal_oxygen']}%\n"
        )

        # 로그 파일에 기록
        with open('./3주차/sensor_log.txt', 'a',encoding='utf-8') as log_file:
            log_file.write(log_line)

        return self.env_values
    
# 인스턴스 생성 및 테스트
if __name__ == '__main__':
    ds = DummySensor()
    ds.set_env()
    values = ds.get_env()

    print('Dummy Sensor Environment Values:')
    for key, value in values.items():
        print(f"{key}: {value}")