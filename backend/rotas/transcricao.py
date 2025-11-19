"""
Rotas de Transcrição - Utiliza fast-whisper para transcrever áudio de vídeos
"""

from flask import Blueprint, request, jsonify
from faster_whisper import WhisperModel
import os
import sys

# Adiciona o diretório raiz ao path para importar utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.persistencia import persistencia

transcricao_bp = Blueprint('transcricao', __name__)

# Inicializa o modelo Whisper (lazy loading)
_modelo = None

def obter_modelo():
    """Obtém o modelo Whisper (inicializa apenas quando necessário)"""
    global _modelo
    if _modelo is None:
        if os.environ.get("USE_CUDA"):
            _modelo = WhisperModel("small", device="cuda", compute_type="float16")
        else:
            _modelo = WhisperModel("small", device="cpu", compute_type="float32")
    return _modelo

@transcricao_bp.route('/transcricao', methods=['POST'])
def transcrever_audio():
    """Transcreve o áudio de um vídeo usando fast-whisper"""
    try:
        data = request.json
        caminho_audio = data.get('audio_path')
        video_id = data.get('video_id')
        url = data.get('url')

        if not caminho_audio:
            return jsonify({'success': False, 'error': 'Caminho do áudio não fornecido'}), 400

        if not os.path.exists(caminho_audio):
            return jsonify({'success': False, 'error': 'Arquivo de áudio não encontrado'}), 400

        # Verifica se já existe transcrição salva
        if url:
            video_salvo = persistencia.obter_video(url)
            if video_salvo and 'transcricao' in video_salvo:
                transcricao_data = video_salvo['transcricao']
                if transcricao_data.get('texto'):
                    return jsonify({
                        'success': True, 
                        'transcricao': transcricao_data.get('segmentos', []),
                        'texto_completo': transcricao_data.get('texto'),
                        'video_id': video_salvo.get('video_id'),
                        'cache': True
                    })

        # Obtém modelo e transcreve
        modelo = obter_modelo()
        segmentos, info = modelo.transcribe(
            caminho_audio, 
            beam_size=5,
            language="pt",  # Português
            vad_filter=True,  # Filtro de voz ativa
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        transcricao_segmentos = []
        texto_completo = []
        
        for segmento in segmentos:
            transcricao_segmentos.append({
                'inicio': round(segmento.start, 2),
                'fim': round(segmento.end, 2),
                'texto': segmento.text.strip()
            })
            texto_completo.append(segmento.text.strip())

        texto_final = ' '.join(texto_completo)

        # Salva transcrição
        transcricao_data = {
            'segmentos': transcricao_segmentos,
            'texto': texto_final,
            'idioma': info.language,
            'duracao_total': round(info.duration, 2)
        }
        
        if video_id:
            persistencia.atualizar_etapa(video_id, 'transcricao', transcricao_data)
        elif url:
            video_salvo = persistencia.obter_video(url)
            if video_salvo:
                persistencia.atualizar_etapa(video_salvo.get('video_id'), 'transcricao', transcricao_data)

        return jsonify({
            'success': True, 
            'transcricao': transcricao_segmentos,
            'texto_completo': texto_final,
            'video_id': video_id,
            'cache': False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
