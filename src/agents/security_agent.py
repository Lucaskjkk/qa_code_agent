from .base_agent import BaseAgent
from utils.security_scanner import SecurityScanner
from models.analysis_result import AnalysisResult

class SecurityAgent(BaseAgent):
    def __init__(self, llm):
        self.llm = llm
        self.scanner = SecurityScanner()

    def run(self, code: str):
        vulnerabilities = self.scanner.scan(code)
        prompt = f"Analise o seguinte código em busca de vulnerabilidades:\n{code}"
        llm_feedback = self.llm.analyze(prompt)

        return AnalysisResult(
            category="security",
            issues=vulnerabilities,
            llm_feedback=llm_feedback
        )
