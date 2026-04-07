from models.vulnerability import Vulnerability

class SecurityScanner:
    """Scanner simples que procura padrões básicos de insegurança."""

    def scan(self, code: str):
        issues = []
        if "eval(" in code:
            issues.append(Vulnerability("<unknown>", -1, "Uso inseguro de eval()", "high").to_dict())
        if "password" in code.lower():
            issues.append(Vulnerability("<unknown>", -1, "Hardcoded password encontrado", "medium").to_dict())
        return issues
