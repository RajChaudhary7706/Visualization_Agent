import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.utils.runtime_tracker import start_tracing, stop_tracing, get_trace

def run_script(script_path):
    start_tracing()

    with open(script_path) as f:
        code = f.read()
        exec(code, {})

    stop_tracing()

    return get_trace()


# 👇 ADD THIS (IMPORTANT)
if __name__ == "__main__":
    trace = run_script("data/sample_project/app.py")

    for t in trace:
        print(t)