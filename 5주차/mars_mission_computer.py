import platform
import psutil
import json
import os

class MissionComputer:
    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self):
        default_settings = {
            "운영체제": True,
            "운영체제 버전": True,
            "CPU 타입": True,
            "CPU 코어 수": True,
            "메모리 크기(GB)": True,
            "CPU 실시간 사용량(%)": True,
            "메모리 실시간 사용량(%)": True
        }
        if not os.path.exists("./5주차/setting.txt"):
            with open("./5주차/setting.txt", "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=4, ensure_ascii=False)
            return default_settings
        else:
            with open("./5주차/setting.txt", "r", encoding="utf-8") as f:
                return json.load(f)

    def get_mission_computer_info(self):
        info = {}
        if self.settings.get("운영체제", False):
            info["운영체제"] = platform.system()
        if self.settings.get("운영체제 버전", False):
            info["운영체제 버전"] = platform.version()
        if self.settings.get("CPU 타입", False):
            info["CPU 타입"] = platform.processor()
        if self.settings.get("CPU 코어 수", False):
            info["CPU 코어 수"] = psutil.cpu_count(logical=False)
        if self.settings.get("메모리 크기(GB)", False):
            info["메모리 크기(GB)"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)

        return json.dumps(info, indent=4, ensure_ascii=False)

    def get_mission_computer_load(self):
        load = {}
        if self.settings.get("CPU 실시간 사용량(%)", False):
            load["CPU 실시간 사용량(%)"] = psutil.cpu_percent(interval=1)
        if self.settings.get("메모리 실시간 사용량(%)", False):
            load["메모리 실시간 사용량(%)"] = psutil.virtual_memory().percent

        return json.dumps(load, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    runComputer = MissionComputer()

    print("=== 미션 컴퓨터 시스템 정보 ===")
    print(runComputer.get_mission_computer_info())

    print("\n=== 미션 컴퓨터 부하 정보 ===")
    print(runComputer.get_mission_computer_load())
