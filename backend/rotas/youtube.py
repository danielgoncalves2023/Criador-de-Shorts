"""
Rotas YouTube - Extração de informações de vídeos
"""

from flask import Blueprint, request, jsonify
import yt_dlp
import sys
import os
import json

# Adiciona o diretório raiz ao path para importar utils
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from utils.persistencia import persistencia

youtube_bp = Blueprint('youtube', __name__)

@youtube_bp.route('/youtube/info', methods=['POST'])
def youtube_info():
    """Extrai informações básicas de um vídeo do YouTube"""
    try:
        data = request.json
        video_url = data.get('url')

        if not video_url:
            return jsonify({'success': False, 'error': 'URL do vídeo não fornecida'}), 400

        # Verifica se já existe no cache
        video_salvo = persistencia.obter_video(video_url)
        if video_salvo and 'info_video' in video_salvo:
            return jsonify({
                'success': True, 
                'video_info': video_salvo['info_video'],
                'video_id': video_salvo.get('video_id'),
                'cache': True
            })

        # Extrai informações do YouTube
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            
            info = {
                'titulo': info_dict.get('title'),
                'autor': info_dict.get('uploader'),
                'duracao_segundos': info_dict.get('duration'),
                'data_publicacao': info_dict.get('upload_date'),
                'descricao': info_dict.get('description'),
                'url_thumbnail': info_dict.get('thumbnail'),
                'visualizacoes': info_dict.get('view_count'),
                'video_id': info_dict.get('id'),
            }
        
        # Salva no sistema de persistência
        video_id = persistencia.salvar_video(video_url, {'info_video': info})
        persistencia.atualizar_etapa(video_id, 'info_video', info)
        
        return jsonify({
            'success': True, 
            'video_info': info,
            'video_id': video_id,
            'cache': False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@youtube_bp.route('/youtube/estado/<video_id>', methods=['GET'])
def obter_estado_video(video_id):
    """Obtém o estado do processamento de um vídeo"""
    try:
        estado = persistencia.obter_estado_processamento(video_id)
        return jsonify({'success': True, 'estado': estado})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@youtube_bp.route('/youtube/dados/<video_id>', methods=['GET'])
def obter_dados_video(video_id):
    """Obtém todos os dados salvos de um vídeo pelo ID"""
    try:
        video_data = persistencia.obter_video_por_id(video_id)
        if video_data:
            return jsonify({
                'success': True,
                'video_id': video_id,
                'url': video_data.get('url'),
                'info_video': video_data.get('info_video'),
                'audio': video_data.get('audio'),
                'transcricao': video_data.get('transcricao'),
                'analise': video_data.get('analise'),
                'ultima_atualizacao': video_data.get('ultima_atualizacao')
            })
        return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
