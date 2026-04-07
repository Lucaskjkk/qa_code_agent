#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from datetime import datetime

# Garante import do pacote src/
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
import sys
sys.path.append(str(SRC))

from src.core.logger import get_logger
from src.services.bitbucket_service import BitbucketService
from src.services.openrouter_service import OpenRouterService
from src.services.analysis_service import AnalysisService
from src.agents.qa_agent import QACodeAgent
from src.utils.file_parser import FileParser
from src.utils.report_generator import ReportGenerator

logger = get_logger(__name__)

def analyze_local_path(local_path: str):
    logger.info(f"Analisando código local em: {local_path}")
    llm = OpenRouterService()
    analysis = AnalysisService(llm)
    files = FileParser.parse_files(local_path)
    results = analysis.analyze_codebase(files)
    return results

def analyze_bitbucket(repo: str, branch: str):
    logger.info(f"Analisando Bitbucket repo={repo} branch={branch}")
    bitbucket = BitbucketService()
    llm = OpenRouterService()
    analysis = AnalysisService(llm)
    qa_agent = QACodeAgent(bitbucket, analysis)
    # Assume que o QACodeAgent usa workspace do config/env internamente
    results = qa_agent.run(repo, branch)
    return results

def save_report(results, output_dir: Path):
    output_dir.mkdir(exist_ok=True, parents=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = output_dir / f"analysis_{ts}.json"
    ReportGenerator.generate(results, str(outfile))
    logger.info(f"Relatório salvo em: {outfile}")
    print(str(outfile))
    return outfile

def main():
    parser = argparse.ArgumentParser(description="QA Code Agent - Runner")
    src_group = parser.add_mutually_exclusive_group(required=False)
    src_group.add_argument("--local-path", help="Diretório local para analisar (substitui Bitbucket)")
    parser.add_argument("--repo", default=os.getenv("BITBUCKET_REPO_SLUG"), help="Slug do repositório Bitbucket")
    parser.add_argument("--branch", default=os.getenv("BITBUCKET_BRANCH", "main"), help="Branch a analisar")
    parser.add_argument("--output-dir", default=str(ROOT / "outputs"), help="Diretório de saída para relatórios")
    args = parser.parse_args()

    if args.local_path:
        results = analyze_local_path(args.local_path)
    else:
        if not args.repo:
            parser.error("Informe --repo ou use --local-path.")
        results = analyze_bitbucket(args.repo, args.branch)

    save_report(results, Path(args.output_dir))

if __name__ == "__main__":
    main()
