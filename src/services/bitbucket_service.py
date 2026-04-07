"""
Serviço de integração com BitBucket API
"""
import base64
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import aiohttp
from dataclasses import dataclass
from ..core.config import settings
from ..core.logger import get_logger
from ..core.exceptions import BitBucketAPIError

logger = get_logger(__name__)


@dataclass
class FileInfo:
    """Informações de um arquivo do repositório"""
    path: str
    name: str
    size: int
    extension: str
    content: Optional[str] = None
    last_modified: Optional[str] = None


@dataclass
class PullRequest:
    """Informações de um Pull Request"""
    id: int
    title: str
    description: str
    source_branch: str
    destination_branch: str
    state: str
    author: str
    created_on: str
    updated_on: str


class BitBucketService:
    """Serviço para interação com BitBucket API"""
    
    def __init__(self):
        self.base_url = settings.BITBUCKET_BASE_URL
        self.workspace = settings.BITBUCKET_WORKSPACE
        self.repo_slug = settings.BITBUCKET_REPO_SLUG
        self.username = settings.BITBUCKET_USERNAME
        self.app_password = settings.BITBUCKET_APP_PASSWORD
        self.auth_header = self._create_auth_header()
    
    def _create_auth_header(self) -> str:
        """Cria header de autenticação Basic Auth"""
        credentials = f"{self.username}:{self.app_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Faz requisição para a API do BitBucket"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise BitBucketAPIError(
                            f"BitBucket API error: {response.status} - {error_text}"
                        )
                    
                    return await response.json()
        
        except aiohttp.ClientError as e:
            logger.error(f"Error making request to BitBucket: {e}")
            raise BitBucketAPIError(f"Connection error: {e}")
    
    async def get_repository_files(
        self, 
        branch: str = "main",
        path: str = ""
    ) -> List[FileInfo]:
        """Obtém lista de arquivos do repositório"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}/src/{branch}/{path}"
        
        try:
            response = await self._make_request("GET", endpoint)
            files = []
            
            for item in response.get("values", []):
                if item["type"] == "commit_file":
                    file_info = FileInfo(
                        path=item["path"],
                        name=item["path"].split("/")[-1],
                        size=item.get("size", 0),
                        extension=self._get_file_extension(item["path"])
                    )
                    files.append(file_info)
            
            return files
        
        except Exception as e:
            logger.error(f"Error fetching repository files: {e}")
            raise
    
    async def get_file_content(self, file_path: str, branch: str = "main") -> str:
        """Obtém conteúdo de um arquivo específico"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}/src/{branch}/{file_path}"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": self.auth_header}
                async with session.get(
                    f"{self.base_url}/{endpoint}",
                    headers=headers
                ) as response:
                    if response.status >= 400:
                        raise BitBucketAPIError(f"Error fetching file: {response.status}")
                    
                    return await response.text()
        
        except Exception as e:
            logger.error(f"Error fetching file content for {file_path}: {e}")
            raise
    
    async def get_supported_files(self, branch: str = "main") -> List[FileInfo]:
        """Obtém apenas arquivos com extensões suportadas para análise"""
        all_files = await self.get_repository_files(branch)
        
        supported_files = []
        for file_info in all_files:
            if (file_info.extension in settings.SUPPORTED_EXTENSIONS and 
                file_info.size <= settings.MAX_FILE_SIZE_MB * 1024 * 1024):
                
                # Busca o conteúdo do arquivo
                try:
                    content = await self.get_file_content(file_info.path, branch)
                    file_info.content = content
                    supported_files.append(file_info)
                except Exception as e:
                    logger.warning(f"Skipping file {file_info.path}: {e}")
                    continue
        
        return supported_files
    
    async def get_pull_requests(self, state: str = "OPEN") -> List[PullRequest]:
        """Obtém lista de Pull Requests"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}/pullrequests"
        params = {"state": state}
        
        try:
            response = await self._make_request("GET", endpoint, params=params)
            pull_requests = []
            
            for pr_data in response.get("values", []):
                pr = PullRequest(
                    id=pr_data["id"],
                    title=pr_data["title"],
                    description=pr_data.get("description", ""),
                    source_branch=pr_data["source"]["branch"]["name"],
                    destination_branch=pr_data["destination"]["branch"]["name"],
                    state=pr_data["state"],
                    author=pr_data["author"]["display_name"],
                    created_on=pr_data["created_on"],
                    updated_on=pr_data["updated_on"]
                )
                pull_requests.append(pr)
            
            return pull_requests
        
        except Exception as e:
            logger.error(f"Error fetching pull requests: {e}")
            raise
    
    async def get_pr_diff_files(self, pr_id: int) -> List[FileInfo]:
        """Obtém arquivos modificados em um Pull Request"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}/pullrequests/{pr_id}/diffstat"
        
        try:
            response = await self._make_request("GET", endpoint)
            modified_files = []
            
            for file_data in response.get("values", []):
                if file_data["status"] in ["modified", "added"]:
                    file_path = file_data["new"]["path"]
                    extension = self._get_file_extension(file_path)
                    
                    if extension in settings.SUPPORTED_EXTENSIONS:
                        # Busca conteúdo do arquivo da branch source do PR
                        pr_info = await self.get_pull_request(pr_id)
                        content = await self.get_file_content(
                            file_path, 
                            pr_info.source_branch
                        )
                        
                        file_info = FileInfo(
                            path=file_path,
                            name=file_path.split("/")[-1],
                            size=len(content.encode()),
                            extension=extension,
                            content=content
                        )
                        modified_files.append(file_info)
            
            return modified_files
        
        except Exception as e:
            logger.error(f"Error fetching PR diff files: {e}")
            raise
    
    async def get_pull_request(self, pr_id: int) -> PullRequest:
        """Obtém informações detalhadas de um Pull Request"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}/pullrequests/{pr_id}"
        
        try:
            pr_data = await self._make_request("GET", endpoint)
            
            return PullRequest(
                id=pr_data["id"],
                title=pr_data["title"],
                description=pr_data.get("description", ""),
                source_branch=pr_data["source"]["branch"]["name"],
                destination_branch=pr_data["destination"]["branch"]["name"],
                state=pr_data["state"],
                author=pr_data["author"]["display_name"],
                created_on=pr_data["created_on"],
                updated_on=pr_data["updated_on"]
            )
        
        except Exception as e:
            logger.error(f"Error fetching pull request {pr_id}: {e}")
            raise
    
    async def create_pr_comment(
        self, 
        pr_id: int, 
        content: str,
        line_to: Optional[int] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cria comentário em um Pull Request"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}/pullrequests/{pr_id}/comments"
        
        comment_data = {
            "content": {
                "raw": content,
                "markup": "markdown"
            }
        }
        
        # Se for comentário em linha específica
        if line_to and file_path:
            comment_data["inline"] = {
                "to": line_to,
                "path": file_path
            }
        
        try:
            return await self._make_request("POST", endpoint, json_data=comment_data)
        
        except Exception as e:
            logger.error(f"Error creating PR comment: {e}")
            raise
    
    def _get_file_extension(self, file_path: str) -> str:
        """Extrai extensão do arquivo"""
        return "." + file_path.split(".")[-1] if "." in file_path else ""
    
    async def health_check(self) -> bool:
        """Verifica se a conexão com BitBucket está funcionando"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}"
        
        try:
            await self._make_request("GET", endpoint)
            return True
        except Exception as e:
            logger.error(f"BitBucket health check failed: {e}")
            return False