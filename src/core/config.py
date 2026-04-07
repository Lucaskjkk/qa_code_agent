import os
from typing import List, Dict, Any
from pydantic import BaseSettings, Field
from dataclasses import dataclass


class Settings(BaseSettings):
    """Configurações principais do sistema"""
    
    # API Keys
    OPENROUTER_API_KEY: str = Field(..., env="OPENROUTER_API_KEY")
    BITBUCKET_USERNAME: str = Field(..., env="BITBUCKET_USERNAME")
    BITBUCKET_APP_PASSWORD: str = Field(..., env="BITBUCKET_APP_PASSWORD")
    QODO_API_KEY: str = Field(default="", env="QODO_API_KEY")
    
    # BitBucket Configuration
    BITBUCKET_WORKSPACE: str = Field(..., env="BITBUCKET_WORKSPACE")
    BITBUCKET_REPO_SLUG: str = Field(..., env="BITBUCKET_REPO_SLUG")
    BITBUCKET_BASE_URL: str = Field(default="https://api.bitbucket.org/2.0")
    
    # OpenRouter Configuration
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = Field(default="anthropic/claude-3-sonnet")
    MAX_TOKENS: int = Field(default=4000)
    TEMPERATURE: float = Field(default=0.1)
    
    # Analysis Configuration
    SUPPORTED_EXTENSIONS: List[str] = Field(
        default=[".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".php"]
    )
    MAX_FILE_SIZE_MB: int = Field(default=5)
    ANALYSIS_TIMEOUT: int = Field(default=300)  # 5 minutes
    
    # Security Patterns
    VULNERABILITY_PATTERNS: Dict[str, List[str]] = Field(
        default={
            "sql_injection": [
                "SELECT.*FROM.*WHERE.*=.*\\$",
                "INSERT.*INTO.*VALUES.*\\$",
                "UPDATE.*SET.*WHERE.*=.*\\$"
            ],
            "xss": [
                "innerHTML.*=.*\\+",
                "document.write\\(",
                "eval\\("
            ],
            "hardcoded_secrets": [
                "password\\s*=\\s*['\"][^'\"]+['\"]",
                "api_key\\s*=\\s*['\"][^'\"]+['\"]",
                "secret\\s*=\\s*['\"][^'\"]+['\"]"
            ]
        }
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Performance
    CONCURRENT_ANALYSES: int = Field(default=3)
    CACHE_TTL: int = Field(default=3600)  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@dataclass
class AnalysisConfig:
    """Configuração específica para análise de código"""
    check_security: bool = True
    check_performance: bool = True
    check_maintainability: bool = True
    check_testing: bool = True
    include_suggestions: bool = True
    severity_threshold: str = "medium"  # low, medium, high, critical


@dataclass
class ReportConfig:
    """Configuração para geração de relatórios"""
    format: str = "json"  # json, markdown, html
    include_code_snippets: bool = True
    max_snippet_lines: int = 10
    include_fix_suggestions: bool = True


# Instância global das configurações
settings = Settings()

# Configurações padrão
DEFAULT_ANALYSIS_CONFIG = AnalysisConfig()
DEFAULT_REPORT_CONFIG = ReportConfig()