import multiprocessing
import sys
import traceback
from contextlib import redirect_stdout
import io

def safe_exec(code, result_queue):
    try:
        f = io.StringIO()
        with redirect_stdout(f):
            exec(code, {'__builtins__': __builtins__, 'print': print})
        result_queue.put((f.getvalue(), None))
    except Exception as e:
        result_queue.put((None, str(e) + "\n" + traceback.format_exc()))

def evaluate_code(code, timeout=5):
    result_queue = multiprocessing.Queue()

    process = multiprocessing.Process(target=safe_exec, args=(code, result_queue))
    process.start()

    process.join(timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        return "Error: Execution timed out."

    if not result_queue.empty():
        output, error = result_queue.get()
        print(f"Output: {output}")
        print(f"Error: {error}")
        if error:
            return f"Error: {error}"
        return output
    else:
        return "Error: No output or error retrieved from the execution."