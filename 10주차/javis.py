import argparse
import os
import subprocess
import sys
from datetime import datetime

DEFAULT_RECORDS_DIR = os.path.join(os.path.dirname(__file__), "records")

def record_audio(records_dir=DEFAULT_RECORDS_DIR):
    os.makedirs(records_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = os.path.join(records_dir, f"{ts}.wav")
    if sys.platform.startswith("win"):
        cmd = ["ffmpeg","-y","-f","dshow","-i","audio=default", out]
    elif sys.platform.startswith("darwin"):
        cmd = ["ffmpeg","-y","-f","avfoundation","-i",":0", out]
    else:
        cmd = ["arecord","-f","cd","-t","wav", out]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass
    print(out)


def list_recordings(start, end, records_dir=DEFAULT_RECORDS_DIR):
    try:
        sd = datetime.strptime(start, "%Y-%m-%d").date()
        ed = datetime.strptime(end, "%Y-%m-%d").date()
    except:
        return
    if not os.path.exists(records_dir):
        return
    fs = []
    for f in os.listdir(records_dir):
        if not f.endswith('.wav'): continue
        try:
            d = datetime.strptime(os.path.splitext(f)[0], "%Y%m%d-%H%M%S").date()
            if sd <= d <= ed:
                fs.append((d, f))
        except:
            pass
    for _, f in sorted(fs):
        print(f)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("record")
    lp = sp.add_parser("list")
    lp.add_argument("start")
    lp.add_argument("end")
    a = p.parse_args()
    if a.cmd == "record":
        record_audio()
    else:
        list_recordings(a.start, a.end)

if __name__ == "__main__":
    main()
