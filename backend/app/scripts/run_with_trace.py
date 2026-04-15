# import sys
# import os

# from app.utils.runtime_tracker import start_tracing, stop_tracing, get_trace


# def run_script(script_path):
#     trace = []

#     try:
#         # ✅ Fix import issues (VERY IMPORTANT)
#         script_dir = os.path.dirname(script_path)
#         sys.path.insert(0, script_dir)

#         # ✅ Change working directory
#         os.chdir(script_dir)

#         start_tracing()

#         # ✅ Execute safely
#         with open(script_path, "r", encoding="utf-8") as f:
#             code = compile(f.read(), script_path, 'exec')
#             exec(code, {"__name__": "__main__"})

#         stop_tracing()

#         trace = get_trace()

#     except Exception as e:
#         print(f"🔥 Runtime execution error: {e}")

#     finally:
#         # cleanup
#         if script_dir in sys.path:
#             sys.path.remove(script_dir)

#     return trace


# # ✅ TEST BLOCK
# if __name__ == "__main__":
#     trace = run_script("data/sample_project/app.py")

#     print("\n🔥 TRACE OUTPUT:")
#     for t in trace:
#         print(t)



import sys
import os
import traceback
import multiprocessing

from app.utils.runtime_tracker import start_tracing, stop_tracing, get_trace


def _run_in_process(script_path, return_dict):
    try:
        script_dir = os.path.dirname(script_path)

        # isolate environment
        sys.path.insert(0, script_dir)

        start_tracing()

        with open(script_path, "r", encoding="utf-8") as f:
            code = compile(f.read(), script_path, "exec")
            exec(code, {"__name__": "__main__"})

        stop_tracing()

        return_dict["trace"] = get_trace()

    except Exception as e:
        return_dict["error"] = str(e)
        return_dict["trace"] = []


def run_script(script_path, timeout=5):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    process = multiprocessing.Process(
        target=_run_in_process,
        args=(script_path, return_dict)
    )

    process.start()
    process.join(timeout)

    if process.is_alive():
        process.terminate()
        print("⚠️ Script execution timed out")
        return []

    if "error" in return_dict:
        print("🔥 Runtime error:", return_dict["error"])

    return return_dict.get("trace", [])


# ✅ TEST
if __name__ == "__main__":
    trace = run_script("data/sample_project/app.py")

    print("\n🔥 TRACE OUTPUT:")
    for t in trace:
        print(t)