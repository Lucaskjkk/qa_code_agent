from .base_agent import BaseAgent
from models.analysis_result import AnalysisResult

class CodeReviewAgent(BaseAgent):
    def __init__(self, llm):
        self.llm = llm

    def run(self, code: str):
        prompt = f"Faça uma revisão de qualidade do seguinte código:\n{code}"
        feedback = self.llm.analyze(prompt)

        return AnalysisResult(
            category="review",
            issues=[],
            llm_feedback=feedback
        )
