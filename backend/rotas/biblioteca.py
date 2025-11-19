"""
Rotas da Biblioteca - Lista vídeos processados
"""

from flask import Blueprint, jsonify
import os
import sys

# Adiciona o diretório raiz ao path para importar utils
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from utils.persistencia import persistencia

biblioteca_bp = Blueprint('biblioteca', __name__)

@biblioteca_bp.route('/biblioteca/listar', methods=['GET'])
def listar_videos():
    """Lista todos os vídeos processados"""
    try:
        videos = persistencia.listar_videos()
        
        # Enriquece com informações adicionais
        videos_enriquecidos = []
        for video in videos:
            video_id = video.get('video_id') or video.get('id')
            if video_id:
                dados_completos = persistencia.obter_video_por_id(video_id)
                if dados_completos:
                    info_video = dados_completos.get('info_video', {})
                    videos_enriquecidos.append({
                        'video_id': video_id,
                        'url': dados_completos.get('url', video.get('url', '')),
                        'titulo': info_video.get('titulo', video.get('titulo', 'Sem título')),
                        'ultima_atualizacao': dados_completos.get('ultima_atualizacao', video.get('ultima_atualizacao', '')),
                        'thumbnail': info_video.get('url_thumbnail', ''),
                        'estado': persistencia.obter_estado_processamento(video_id)
                    })
        
        return jsonify({
            'success': True,
            'videos': videos_enriquecidos,
            'total': len(videos_enriquecidos)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

