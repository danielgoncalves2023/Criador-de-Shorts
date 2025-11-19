"""
Rota para processar vídeo completo - orquestra todas as etapas
"""

from flask import Blueprint, request, jsonify
import os
import sys

# Adiciona o diretório raiz ao path para importar utils
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from utils.persistencia import persistencia

processar_bp = Blueprint('processar', __name__)

@processar_bp.route('/processar-video', methods=['POST'])
def processar_video_completo():
    """
    Processa um vídeo completo: busca info, baixa áudio, transcreve e analisa
    """
    try:
        data = request.json
        url = data.get('url')
        video_id = data.get('video_id')

        if not url and not video_id:
            return jsonify({'success': False, 'error': 'URL ou ID do vídeo não fornecidos'}), 400

        # Obtém ou cria dados do vídeo
        if url:
            video_salvo = persistencia.obter_video(url)
            if video_salvo:
                video_id = video_salvo.get('video_id')
            else:
                # Precisa buscar informações primeiro
                return jsonify({
                    'success': False,
                    'error': 'Vídeo não encontrado. Busque informações primeiro.'
                }), 400
        else:
            # Busca por video_id
            video_salvo = persistencia.obter_video_por_id(video_id)
            if video_salvo:
                url = video_salvo.get('url')
            else:
                return jsonify({
                    'success': False,
                    'error': 'Vídeo não encontrado'
                }), 404

        if not video_salvo:
            return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404

        estado = persistencia.obter_estado_processamento(video_id)
        
        resultado = {
            'video_id': video_id,
            'url': url,
            'estado': estado,
            'etapas_completas': {
                'info_video': estado.get('info_video', False),
                'audio': estado.get('audio', False),
                'transcricao': estado.get('transcricao', False),
                'analise': estado.get('analise', False)
            }
        }

        return jsonify({
            'success': True,
            **resultado
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

