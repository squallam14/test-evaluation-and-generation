import re


def get_code_from_response(text: str) -> str:
    match = re.search(r'```(?:\w+\n)?(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return None