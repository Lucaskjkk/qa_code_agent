from agents.security_agent import SecurityAgent
from agents.code_review_agent import CodeReviewAgent
from utils.file_parser import FileParser

class AnalysisService:
    def __init__(self, llm):
        self.security_agent = SecurityAgent(llm)
        self.review_agent = CodeReviewAgent(llm)

    def analyze_codebase(self, files: dict):
        results = []
        for filename, code in files.items():
            results.append(self.security_agent.run(code))
            results.append(self.review_agent.run(code))
        return results
