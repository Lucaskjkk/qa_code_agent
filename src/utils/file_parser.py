import os

class FileParser:
    @staticmethod
    def parse_files(path: str, extensions=(".py", ".js", ".ts")):
        codebase = {}
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(extensions):
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        codebase[f] = file.read()
        return codebase
