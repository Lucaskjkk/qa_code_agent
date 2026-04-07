class QAAgentError(Exception):
    """Erro genérico do agente QA."""
    pass


class ConfigError(QAAgentError):
    """Erro de configuração."""
    pass


class ServiceError(QAAgentError):
    """Erro em serviços externos (Bitbucket, OpenRouter, etc)."""
    pass
