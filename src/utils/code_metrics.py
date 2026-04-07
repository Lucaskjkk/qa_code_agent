def calculate_metrics(code: str):
    lines = code.splitlines()
    loc = len(lines)
    complexity = sum(1 for l in lines if "if " in l or "for " in l or "while " in l)
    return {"loc": loc, "complexity": complexity}
