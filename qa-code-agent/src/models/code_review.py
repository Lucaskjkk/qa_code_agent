class CodeReview:
    def __init__(self, file: str, comments: list):
        self.file = file
        self.comments = comments

    def to_dict(self):
        return {
            "file": self.file,
            "comments": self.comments,
        }
