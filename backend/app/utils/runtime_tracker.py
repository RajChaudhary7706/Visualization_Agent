import sys

call_log = []

def trace_calls(frame, event, arg):
    if event == "call":
        code = frame.f_code
        func_name = code.co_name
        file_name = code.co_filename

        call_log.append((file_name, func_name))

    return trace_calls

def start_tracing():
    sys.settrace(trace_calls)

def stop_tracing():
    sys.settrace(None)

def get_trace():
    return call_log