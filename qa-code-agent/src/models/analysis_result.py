class AnalysisResult:
    def __init__(self, category: str, issues: list, llm_feedback: str):
        self.category = category
        self.issues = issues
        self.llm_feedback = llm_feedback

    def to_dict(self):
        return {
            "category": self.category,
            "issues": self.issues,
            "llm_feedback": self.llm_feedback,
        }
