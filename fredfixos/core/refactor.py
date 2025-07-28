# fredfixos/core/refactor.py
def refactor_file(file_path):
    with open(file_path, "r") as f:
        code = f.read()
    return f"[Refactored output of {file_path}]:\n{code}"