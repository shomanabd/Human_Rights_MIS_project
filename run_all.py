import subprocess
import threading
import sys
import os
import json


def run_fastapi():
    print("[FASTAPI] Starting backend server...")
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload"])


def run_streamlit():
    print("[STREAMLIT] Launching frontend interface...")
    subprocess.run(["streamlit", "run", "streamlit_app.py"])


if __name__ == "__main__":
    os.chdir(
        os.path.dirname(os.path.abspath(__file__))
    )  # ensure script runs from project root
    print("Launching Human Rights MIS ...\n")

    t1 = threading.Thread(target=run_fastapi)
    t2 = threading.Thread(target=run_streamlit)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
