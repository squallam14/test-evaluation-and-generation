import multiprocessing
import sys
import traceback
from contextlib import redirect_stdout
import io


def safe_exec(code, result_queue):
    try:
        f = io.StringIO()
        with redirect_stdout(f):
            exec(code, {"__builtins__": __builtins__, "print": print})
        result_queue.put((f.getvalue(), None))
    except Exception as e:
        result_queue.put((None, str(e) + "\n" + traceback.format_exc()))


def evaluate_code(code, timeout=5) -> dict:
    return_data = {"output": None, "error": None}
    result_queue = multiprocessing.Queue()

    process = multiprocessing.Process(target=safe_exec, args=(code, result_queue))
    process.start()

    process.join(timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        return_data["output"] = None
        return_data["error"] = "Execution timed out."
        return return_data

    if not result_queue.empty():
        output, error = result_queue.get()
        return_data["output"] = output
        return_data["error"] = error
        return return_data
    else:
        return_data["output"] = None
        return_data["error"] = "No output was returned."
        return return_data
