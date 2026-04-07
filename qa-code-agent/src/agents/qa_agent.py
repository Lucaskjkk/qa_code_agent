"""
Agente principal de QA (Quality Assurance) para análise de código
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from ..services.bitbucket_service import BitBucketService, FileInfo
from ..services.openrouter_service import OpenRouterService, ChatMessage
from ..models.analysis_result import AnalysisResult, Issue, Suggestion
from ..utils.security_scanner import SecurityScanner
from ..utils.code_metrics import CodeMetrics
from ..utils.report_generator import ReportGenerator
from ..core.config import settings, AnalysisConfig
from ..core.logger import get_logger
from ..core.exceptions import AnalysisError

logger = get_logger(__name__)


@dataclass
class AnalysisContext:
    """Contexto da análise"""
    repository: str
    branch: str
    pull_request_id: Optional[int] = None
    files_to_analyze: List[str] = None
    analysis_config: AnalysisConfig = None
    
    def __post_init__(self):
        if self.analysis_config is None:
            self.analysis_config = AnalysisConfig()
        if self.files_to_analyze is None:
            self.files_to_analyze = []


class QAAgent:
    """Agente principal para análise de qualidade de código"""
    
    def __init__(self):
        self.bitbucket_service = BitBucketService()
        self.openrouter_service = OpenRouterService()
        self.security_scanner = SecurityScanner()
        self.code_metrics = CodeMetrics()
        self.report_generator = ReportGenerator()
    
    async def analyze_repository(
        self,
        context: AnalysisContext
    ) -> AnalysisResult:
        """Análise completa de um repositório"""
        
        logger.info(f"Starting repository analysis: {context.repository}")
        
        try:
            # 1. Obter arquivos para análise
            files_to_analyze = await self._get_files_to_analyze(context)
            
            if not files_to_analyze:
                logger.warning("No files found for analysis")
                return AnalysisResult(
                    repository=context.repository,
                    branch=context.branch,
                    analysis_date=datetime.now(),
                    files_analyzed=[],
                    issues_found=[],
                    suggestions=[],
                    summary={"total_files": 0, "total_issues": 0}
                )
            
            # 2. Executar análises em paralelo
            analysis_results = await self._execute_parallel_analysis(
                files_to_analyze, context
            )
            
            # 3. Consolidar resultados
            final_result = await self._consolidate_results(
                analysis_results, context
            )
            
            logger.info(f"Analysis completed: {len(final_result.issues_found)} issues found")
            return final_result
            
        except Exception as e:
            logger.error(f"Error during repository analysis: {e}")
            raise AnalysisError(f"Repository analysis failed: {e}")
    
    async def analyze_pull_request(
        self,
        pr_id: int,
        context: AnalysisContext
    ) -> AnalysisResult:
        """Análise específica de um Pull Request"""
        
        logger.info(f"Starting pull request analysis: PR #{pr_id}")
        context.pull_request_id = pr_id
        
        try:
            # Obter arquivos modificados no PR
            modified_files = await self.bitbucket_service.get_pr_diff_files(pr_id)
            
            if not modified_files:
                logger.warning(f"No modified files found in PR #{pr_id}")
                return AnalysisResult(
                    repository=context.repository,
                    branch=context.branch,
                    pull_request_id=pr_id,
                    analysis_date=datetime.now(),
                    files_analyzed=[],
                    issues_found=[],
                    suggestions=[],
                    summary={"total_files": 0, "total_issues": 0}
                )
            
            # Filtrar apenas arquivos suportados
            supported_files = [
                f for f in modified_files 
                if f.extension in settings.SUPPORTED_EXTENSIONS
            ]
            
            # Executar análises
            analysis_results = await self._execute_parallel_analysis(
                supported_files, context
            )
            
            # Consolidar resultados
            final_result = await self._consolidate_results(
                analysis_results, context
            )
            
            logger.info(f"PR analysis completed: {len(final_result.issues_found)} issues found")
            return final_result
            
        except Exception as e:
            logger.error(f"Error during PR analysis: {e}")
            raise AnalysisError(f"PR analysis failed: {e}")
    
    async def _get_files_to_analyze(
        self, 
        context: AnalysisContext
    ) -> List[FileInfo]:
        """Obtém lista de arquivos para análise"""
        
        if context.files_to_analyze:
            # Arquivos específicos solicitados
            files = []
            for file_path in context.files_to_analyze:
                try:
                    content = await self.bitbucket_service.get_file_content(
                        file_path, context.branch
                    )
                    file_info = FileInfo(
                        path=file_path,
                        name=file_path.split("/")[-1],
                        size=len(content.encode()),
                        extension=self._get_file_extension(file_path),
                        content=content
                    )
                    files.append(file_info)
                except Exception as e:
                    logger.warning(f"Could not analyze file {file_path}: {e}")
            return files
        else:
            # Todos os arquivos suportados
            return await self.bitbucket_service.get_supported_files(context.branch)
    
    async def _execute_parallel_analysis(
        self,
        files: List[FileInfo],
        context: AnalysisContext
    ) -> List[Dict[str, Any]]:
        """Executa análises em paralelo com controle de concorrência"""
        
        semaphore = asyncio.Semaphore(settings.CONCURRENT_ANALYSES)
        
        async def analyze_single_file(file_info: FileInfo) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self._analyze_file_comprehensive(file_info, context)
                except Exception as e:
                    logger.error(f"Error analyzing file {file_info.path}: {e}")
                    return {
                        "file_path": file_info.path,
                        "error": str(e),
                        "issues": [],
                        "suggestions": []
                    }
        
        tasks = [analyze_single_file(file_info) for file_info in files]
        return await asyncio.gather(*tasks)
    
    async def _analyze_file_comprehensive(
        self,
        file_info: FileInfo,
        context: AnalysisContext
    ) -> Dict[str, Any]:
        """Análise abrangente de um arquivo"""
        
        logger.debug(f"Analyzing file: {file_info.path}")
        
        file_issues = []
        file_suggestions = []
        language = self._detect_language(file_info.extension)
        
        # 1. Análise de segurança (se habilitada)
        if context.analysis_config.check_security:
            security_issues = await self._analyze_security(
                file_info, language
            )
            file_issues.extend(security_issues)
        
        # 2. Análise de qualidade (se habilitada)
        if context.analysis_config.check_maintainability:
            quality_issues, quality_suggestions = await self._analyze_quality(
                file_info, language
            )
            file_issues.extend(quality_issues)
            file_suggestions.extend(quality_suggestions)
        
        # 3. Análise de performance (se habilitada)
        if context.analysis_config.check_performance:
            performance_issues = await self._analyze_performance(
                file_info, language
            )
            file_issues.extend(performance_issues)
        
        # 4. Análise de testes (se habilitada)
        if context.analysis_config.check_testing:
            testing_suggestions = await self._analyze_testing(
                file_info, language
            )
            file_suggestions.extend(testing_suggestions)
        
        return {
            "file_path": file_info.path,
            "language": language,
            "issues": file_issues,
            "suggestions": file_suggestions,
            "metrics": self.code_metrics.calculate_metrics(file_info.content)
        }
    
    async def _analyze_security(
        self,
        file_info: FileInfo,
        language: str
    ) -> List[Issue]:
        """Análise de segurança usando IA + scanner de padrões"""
        
        issues = []
        
        # 1. Scanner de padrões (rápido)
        pattern_issues = self.security_scanner.scan_patterns(
            file_info.content, file_info.path
        )
        issues.extend(pattern_issues)
        
        # 2. Análise com IA (mais profunda)
        try:
            ai_response = await self.openrouter_service.analyze_code_security(
                file_info.content, file_info.path, language
            )
            
            # Parse da resposta JSON
            ai_issues = self._parse_ai_security_response(ai_response.content, file_info.path)
            issues.extend(ai_issues)
            
        except Exception as e:
            logger.error(f"AI security analysis failed for {file_info.path}: {e}")
        
        return issues
    
    async def _analyze_quality(
        self,
        file_info: FileInfo,
        language: str
    ) -> tuple[List[Issue], List[Suggestion]]:
        """Análise de qualidade de código"""
        
        issues = []
        suggestions = []
        
        try:
            ai_response = await self.openrouter_service.analyze_code_quality(
                file_info.content, file_info.path, language
            )
            
            parsed_result = self._parse_ai_quality_response(ai_response.content, file_info.path)
            issues.extend(parsed_result["issues"])
            suggestions.extend(parsed_result["suggestions"])
            
        except Exception as e:
            logger.error(f"AI quality analysis failed for {file_info.path}: {e}")
        
        return issues, suggestions
    
    async def _analyze_performance(
        self,
        file_info: FileInfo,
        language: str
    ) -> List[Issue]:
        """Análise de performance"""
        
        # Implementar análise de performance básica
        # Por enquanto, usar métricas simples
        issues = []
        
        metrics = self.code_metrics.calculate_metrics(file_info.content)
        
        # Complexidade ciclomática alta
        if metrics.get("cyclomatic_complexity", 0) > 10:
            issues.append(Issue(
                type="performance",
                severity="medium",
                title="Alta complexidade ciclomática",
                description=f"Complexidade ciclomática: {metrics['cyclomatic_complexity']}",
                file_path=file_info.path,
                line_number=None,
                code_snippet="",
                suggestion="Considere quebrar este método/função em partes menores"
            ))
        
        return issues
    
    async def _analyze_testing(
        self,
        file_info: FileInfo,
        language: str
    ) -> List[Suggestion]:
        """Análise de testabilidade e sugestões de testes"""
        
        suggestions = []
        
        try:
            ai_response = await self.openrouter_service.analyze_code_testing(
                file_info.content, file_info.path, language
            )
            
            suggestions = self._parse_ai_testing_response(ai_response.content, file_info.path)
            
        except Exception as e:
            logger.error(f"AI testing analysis failed for {file_info.path}: {e}")
        
        return suggestions
    
    async def _consolidate_results(
        self,
        analysis_results: List[Dict[str, Any]],
        context: AnalysisContext
    ) -> AnalysisResult:
        """Consolida todos os resultados de análise"""
        
        all_issues = []
        all_suggestions = []
        files_analyzed = []
        
        for result in analysis_results:
            if "error" not in result:
                files_analyzed.append(result["file_path"])
                all_issues.extend(result.get("issues", []))
                all_suggestions.extend(result.get("suggestions", []))
        
        # Filtrar por severidade
        filtered_issues = [
            issue for issue in all_issues
            if self._meets_severity_threshold(issue, context.analysis_config.severity_threshold)
        ]
        
        # Calcular resumo
        summary = {
            "total_files": len(files_analyzed),
            "total_issues": len(filtered_issues),
            "critical_issues": len([i for i in filtered_issues if i.severity == "critical"]),
            "high_issues": len([i for i in filtered_issues if i.severity == "high"]),
            "medium_issues": len([i for i in filtered_issues if i.severity == "medium"]),
            "low_issues": len([i for i in filtered_issues if i.severity == "low"]),
            "total_suggestions": len(all_suggestions)
        }
        
        return AnalysisResult(
            repository=context.repository,
            branch=context.branch,
            pull_request_id=context.pull_request_id,
            analysis_date=datetime.now(),
            files_analyzed=files_analyzed,
            issues_found=filtered_issues,
            suggestions=all_suggestions[:50],  # Limitar sugestões
            summary=summary
        )
    
    def _parse_ai_security_response(self, response: str, file_path: str) -> List[Issue]:
        """Parse da resposta de segurança da IA"""
        try:
            data = json.loads(response)
            issues = []
            
            for vuln in data.get("vulnerabilities", []):
                issues.append(Issue(
                    type="security",
                    severity=vuln.get("severity", "medium").lower(),
                    title=vuln.get("title", "Security Issue"),
                    description=vuln.get("description", ""),
                    file_path=file_path,
                    line_number=vuln.get("line", None),
                    code_snippet=vuln.get("code_snippet", ""),
                    suggestion=vuln.get("fix_suggestion", "")
                ))
            
            return issues
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI security response for {file_path}")
            return []
    
    def _parse_ai_quality_response(self, response: str, file_path: str) -> Dict[str, List]:
        """Parse da resposta de qualidade da IA"""
        try:
            data = json.loads(response)
            issues = []
            suggestions = []
            
            for item in data.get("quality_issues", []):
                issues.append(Issue(
                    type="quality",
                    severity=item.get("severity", "medium").lower(),
                    title=item.get("title", "Quality Issue"),
                    description=item.get("description", ""),
                    file_path=file_path,
                    line_number=item.get("line", None),
                    code_snippet=item.get("code_snippet", ""),
                    suggestion=item.get("improvement", "")
                ))
            
            for item in data.get("suggestions", []):
                suggestions.append(Suggestion(
                    type="improvement",
                    title=item.get("title", "Improvement"),
                    description=item.get("description", ""),
                    file_path=file_path,
                    code_example=item.get("example", "")
                ))
            
            return {"issues": issues, "suggestions": suggestions}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI quality response for {file_path}")
            return {"issues": [], "suggestions": []}
    
    def _parse_ai_testing_response(self, response: str, file_path: str) -> List[Suggestion]:
        """Parse da resposta de testes da IA"""
        try:
            data = json.loads(response)
            suggestions = []
            
            for item in data.get("test_suggestions", []):
                suggestions.append(Suggestion(
                    type="testing",
                    title=item.get("title", "Test Suggestion"),
                    description=item.get("description", ""),
                    file_path=file_path,
                    code_example=item.get("test_code", "")
                ))
            
            return suggestions
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI testing response for {file_path}")
            return []
    
    def _meets_severity_threshold(self, issue: Issue, threshold: str) -> bool:
        """Verifica se o issue atende o threshold de severidade"""
        severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return severity_levels.get(issue.severity, 0) >= severity_levels.get(threshold, 1)
    
    def _detect_language(self, extension: str) -> str:
        """Detecta linguagem pelo arquivo"""
        language_map = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".php": "php"
        }
        return language_map.get(extension, "unknown")
    
    def _get_file_extension(self, file_path: str) -> str:
        """Extrai extensão do arquivo"""
        return "." + file_path.split(".")[-1] if "." in file_path else ""
    
    async def health_check(self) -> Dict[str, bool]:
        """Verifica saúde de todos os serviços"""
        return {
            "bitbucket": await self.bitbucket_service.health_check(),
            "openrouter": await self.openrouter_service.health_check()
        }