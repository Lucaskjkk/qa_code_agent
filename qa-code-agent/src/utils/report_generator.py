import json

class ReportGenerator:
    @staticmethod
    def generate(results, output_file="analysis_report.json"):
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in results], f, indent=4)
        return output_file
