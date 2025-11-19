"""
Sistema de persistência local para salvar o progresso do processamento de vídeos
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Any, List
from pathlib import Path


class Persistencia:
    """Gerencia a persistência de dados do processamento de vídeos"""
    
    def __init__(self, base_dir: str = None):
        """
        Inicializa o sistema de persistência
        
        Args:
            base_dir: Diretório base para salvar os dados (padrão: backend/dados)
        """
        backend_dir = Path(__file__).resolve().parent.parent
        projeto_dir = backend_dir.parent

        candidatos: List[Path] = []
        env_dir = os.environ.get("DADOS_DIR")

        if base_dir:
            candidatos.append(Path(base_dir))
        elif env_dir:
            candidatos.append(Path(env_dir))

        candidatos.append(backend_dir / "dados")
        candidatos.append(projeto_dir / "dados")

        # Remove duplicados preservando a ordem
        diretorios = []
        for diretorio in candidatos:
            if diretorio not in diretorios:
                diretorios.append(diretorio)

        if not diretorios:
            diretorios = [backend_dir / "dados"]

        self.diretorios_busca = diretorios
        self.base_dir = self.diretorios_busca[0]
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo principal de índice
        self.indice_path = self.base_dir / "indice.json"
        self._indice_origem: Dict[str, Path] = {}
        self._carregar_indice()
    
    def _carregar_indice(self):
        """Carrega o índice de vídeos processados de todos os diretórios conhecidos"""
        self.indice: Dict[str, Dict[str, Any]] = {}
        self._indice_origem.clear()

        for diretorio in self.diretorios_busca:
            indice_path = diretorio / "indice.json"
            if indice_path.exists():
                try:
                    with open(indice_path, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    for video_id, info in dados.items():
                        if video_id not in self.indice:
                            self.indice[video_id] = info
                            self._indice_origem[video_id] = diretorio
                except Exception:
                    continue
    
    def _salvar_indice(self):
        """Salva o índice de vídeos processados no diretório base"""
        self.indice_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.indice_path, 'w', encoding='utf-8') as f:
            json.dump(self.indice, f, ensure_ascii=False, indent=2)
    
    def _extrair_video_id(self, url: str) -> Optional[str]:
        """Extrai o ID do vídeo de uma URL do YouTube"""
        from urllib.parse import urlparse, parse_qs
        
        try:
            parsed = urlparse(url)
            if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
                if 'youtu.be' in parsed.netloc:
                    video_id = parsed.path.lstrip('/')
                else:
                    video_id = parse_qs(parsed.query).get('v', [None])[0]
                return video_id
        except:
            pass
        return None
    
    def _resolver_caminho_video(self, video_id: str) -> Path:
        """Retorna o caminho do arquivo do vídeo, procurando em todas as pastas conhecidas."""
        for diretorio in self.diretorios_busca:
            video_path = diretorio / f"{video_id}.json"
            if video_path.exists():
                return video_path
        return self.base_dir / f"{video_id}.json"

    def obter_caminho_video(self, video_id: str) -> Path:
        """Garante a existência do diretório e retorna o caminho completo do arquivo do vídeo."""
        video_path = self._resolver_caminho_video(video_id)
        video_path.parent.mkdir(parents=True, exist_ok=True)
        return video_path

    def obter_video_por_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Obtém os dados completos de um vídeo a partir do ID."""
        video_path = self._resolver_caminho_video(video_id)
        if video_path.exists():
            try:
                with open(video_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def obter_video(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Obtém os dados salvos de um vídeo a partir da URL
        """
        video_id = self._extrair_video_id(url)
        if not video_id:
            return None
        
        dados = self.obter_video_por_id(video_id)
        if dados and video_id not in self.indice:
            self.indice[video_id] = {
                'url': url,
                'titulo': dados.get('info_video', {}).get('titulo', 'Sem título'),
                'ultima_atualizacao': dados.get('ultima_atualizacao', datetime.now().isoformat())
            }
            self._indice_origem[video_id] = self._resolver_caminho_video(video_id).parent
            self._salvar_indice()
        return dados
    
    def salvar_video(self, url: str, dados: Dict[str, Any]) -> str:
        """
        Salva os dados de um vídeo
        
        Args:
            url: URL do vídeo do YouTube
            dados: Dicionário com os dados do vídeo
            
        Returns:
            ID do vídeo
        """
        video_id = self._extrair_video_id(url)
        if not video_id:
            raise ValueError("URL inválida: não foi possível extrair o ID do vídeo")
        
        # Adiciona metadados
        dados['video_id'] = video_id
        dados['url'] = url
        dados['ultima_atualizacao'] = datetime.now().isoformat()
        
        # Salva arquivo individual
        video_path = self.obter_caminho_video(video_id)
        with open(video_path, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        self._indice_origem[video_id] = video_path.parent
        
        # Atualiza índice
        self.indice[video_id] = {
            'url': url,
            'titulo': dados.get('info_video', {}).get('titulo', 'Sem título'),
            'ultima_atualizacao': dados['ultima_atualizacao']
        }
        self._salvar_indice()
        
        return video_id
    
    def atualizar_etapa(self, video_id: str, etapa: str, dados_etapa: Dict[str, Any]):
        """
        Atualiza uma etapa específica do processamento
        
        Args:
            video_id: ID do vídeo
            etapa: Nome da etapa (info_video, audio, transcricao, analise, shorts)
            dados_etapa: Dados da etapa
        """
        video_path = self.obter_caminho_video(video_id)

        if video_path.exists():
            try:
                with open(video_path, 'r', encoding='utf-8') as f:
                    video_data = json.load(f)
            except Exception:
                video_data = {'video_id': video_id}
        else:
            video_data = {'video_id': video_id}
        
        video_data[etapa] = dados_etapa
        video_data['ultima_atualizacao'] = datetime.now().isoformat()
        
        with open(video_path, 'w', encoding='utf-8') as f:
            json.dump(video_data, f, ensure_ascii=False, indent=2)
        self._indice_origem[video_id] = video_path.parent
    
    def listar_videos(self) -> list:
        """
        Lista todos os vídeos processados
        
        Returns:
            Lista de dicionários com informações básicas dos vídeos
        """
        videos = []
        for video_id, dados in self.indice.items():
            videos.append({
                'video_id': video_id,
                'id': video_id,  # Alias para compatibilidade
                **dados
            })
        return videos
    
    def obter_estado_processamento(self, video_id: str) -> Dict[str, bool]:
        """
        Obtém o estado do processamento de um vídeo
        
        Returns:
            Dicionário indicando quais etapas foram concluídas
        """
        video_path = self._resolver_caminho_video(video_id)
        
        if not video_path.exists():
            return {
                'info_video': False,
                'audio': False,
                'transcricao': False,
                'analise': False,
                'shorts': False
            }
        
        with open(video_path, 'r', encoding='utf-8') as f:
            video_data = json.load(f)
        
        return {
            'info_video': 'info_video' in video_data,
            'audio': 'audio' in video_data and video_data['audio'].get('caminho_arquivo'),
            'transcricao': 'transcricao' in video_data and video_data['transcricao'].get('texto'),
            'analise': 'analise' in video_data and video_data['analise'].get('sugestoes'),
            'shorts': 'shorts' in video_data and len(video_data.get('shorts', [])) > 0
        }


# Instância global
persistencia = Persistencia()

