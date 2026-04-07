from core.logger import get_logger
from services.bitbucket_service import BitbucketService
from services.openrouter_service import OpenRouterService
from agents.qa_agent import QACodeAgent
from services.analysis_service import AnalysisService

logger = get_logger(__name__)

def main():
    logger.info("Iniciando QA Code Agent...")

    # Inicializa serviços
    bitbucket = BitbucketService()
    llm = OpenRouterService()
    analysis = AnalysisService(llm)

    # Inicializa agente principal
    qa_agent = QACodeAgent(bitbucket, analysis)

    # Executa análise do repositório
    repo = "meu-repo"
    branch = "main"
    resultados = qa_agent.run(repo, branch)

    logger.info("Análise finalizada!")
    for r in resultados:
        print(r.to_dict())

if __name__ == "__main__":
    main()
