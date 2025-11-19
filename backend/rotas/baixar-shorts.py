"""
Rotas de Download de Shorts - Baixa os shorts sugeridos pela IA
"""

from flask import Blueprint, request, jsonify
import os
import subprocess
import sys
import json
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SHORTS_DIR = os.path.join(UPLOAD_DIR, "shorts")
TEMP_VIDEO_TEMPLATE = "{video_id}_temp.mp4"
MIN_SHORT_DURATION = 40
MAX_SHORT_DURATION = 180

# Adiciona o diretório raiz ao path para importar utils
sys.path.insert(0, BASE_DIR)
from utils.persistencia import persistencia

shorts_bp = Blueprint('shorts', __name__)

def _extrair_video_id(url: str):
    """Extrai o ID do vídeo de uma URL do YouTube"""
    from urllib.parse import urlparse, parse_qs
    try:
        parsed = urlparse(url)
        if 'youtu.be' in parsed.netloc:
            return parsed.path.lstrip('/')
        elif 'youtube.com' in parsed.netloc:
            return parse_qs(parsed.query).get("v", [None])[0]
    except:
        pass
    return None

@shorts_bp.route('/shorts/baixar', methods=['POST'])
def baixar_short():
    """Baixa um short específico baseado nos tempos sugeridos"""
    try:
        data = request.json
        video_id = data.get('video_id')
        url = data.get('url')
        inicio_segundos = data.get('inicio_segundos')
        fim_segundos = data.get('fim_segundos')
        titulo_short = data.get('titulo', 'short')
        indice_sugestao = data.get('indice_sugestao', 0)

        if not video_id and not url:
            return jsonify({'success': False, 'error': 'ID do vídeo ou URL não fornecidos'}), 400

        if inicio_segundos is None or fim_segundos is None:
            return jsonify({'success': False, 'error': 'Tempos de início e fim não fornecidos'}), 400

        # Obtém dados do vídeo
        if url:
            video_salvo = persistencia.obter_video(url)
            if not video_salvo:
                return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404
            video_id = video_salvo.get('video_id')
            url_video = url
        else:
            video_salvo = persistencia.obter_video_por_id(video_id)
            if not video_salvo:
                return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404
            url_video = video_salvo.get('url')

        if not url_video:
            return jsonify({'success': False, 'error': 'URL do vídeo não encontrada'}), 400

        duracao_video = video_salvo.get('info_video', {}).get('duracao_segundos')
        inicio_segundos, fim_segundos, duracao = _ajustar_intervalo_descarga(
            inicio_segundos,
            fim_segundos,
            duracao_video
        )
        if duracao < MIN_SHORT_DURATION:
            return jsonify({'success': False, 'error': 'Não foi possível ajustar o intervalo dentro do mínimo exigido'}), 400

        # Define caminho de saída
        os.makedirs(SHORTS_DIR, exist_ok=True)
        
        # Nome do arquivo seguro
        nome_arquivo = f"{video_id}_short_{indice_sugestao}_{int(inicio_segundos)}s.mp4"
        output_path = os.path.join(SHORTS_DIR, nome_arquivo)

        # Verifica se já existe
        if os.path.exists(output_path):
            # Atualiza lista de shorts baixados
            shorts_baixados = video_salvo.get('shorts_baixados', [])
            short_info = {
                'caminho_arquivo': output_path,
                'inicio_segundos': float(inicio_segundos),
                'fim_segundos': float(fim_segundos),
                'duracao_segundos': duracao,
                'titulo': titulo_short,
                'indice_sugestao': indice_sugestao
            }
            
            if not any(s.get('caminho_arquivo') == output_path for s in shorts_baixados):
                shorts_baixados.append(short_info)
                video_salvo['shorts_baixados'] = shorts_baixados
            dados_path = persistencia.obter_caminho_video(video_id)
            with open(dados_path, 'w', encoding='utf-8') as f:
                json.dump(video_salvo, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'caminho_arquivo': output_path,
                'video_id': video_id,
                'cache': True
            })

        temp_path = os.path.join(SHORTS_DIR, TEMP_VIDEO_TEMPLATE.format(video_id=video_id))

        comando_base = _obter_comando_ytdlp()
        if not comando_base:
            return jsonify({
                'success': False,
                'error': 'yt-dlp não encontrado. Instale com: pip install yt-dlp'
            }), 500
        
        # Primeiro baixa o vídeo completo (se não existir)
        if not os.path.exists(temp_path):
            comando_download = comando_base + [
                "-f", "best[height<=1080]",
                "--output", temp_path,
                "--quiet",
                "--no-warnings",
                url_video
            ]
            
            resultado = subprocess.run(comando_download, capture_output=True, text=True, timeout=600)
            if resultado.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Erro ao baixar vídeo: {resultado.stderr or resultado.stdout}'
                }), 500

        # Corta o vídeo usando ffmpeg
        comando_cortar = [
            "ffmpeg",
            "-i", temp_path,
            "-ss", str(inicio_segundos),
            "-t", str(duracao),
            "-c", "copy",  # Copy codec para ser mais rápido
            "-avoid_negative_ts", "make_zero",
            "-y",  # Sobrescreve se existir
            output_path
        ]

        resultado = subprocess.run(comando_cortar, capture_output=True, text=True, timeout=300)
        
        if resultado.returncode != 0:
            # Tenta com re-encoding se copy não funcionar
            comando_cortar_reencode = [
                "ffmpeg",
                "-i", temp_path,
                "-ss", str(inicio_segundos),
                "-t", str(duracao),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "fast",
                "-y",
                output_path
            ]
            
            resultado = subprocess.run(comando_cortar_reencode, capture_output=True, text=True, timeout=600)
            
            if resultado.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Erro ao cortar vídeo: {resultado.stderr or resultado.stdout}'
                }), 500

        if not os.path.exists(output_path):
            return jsonify({'success': False, 'error': 'Arquivo de short não foi gerado.'}), 500

        # Atualiza lista de shorts baixados
        shorts_baixados = video_salvo.get('shorts_baixados', [])
        short_info = {
            'caminho_arquivo': output_path,
            'inicio_segundos': float(inicio_segundos),
            'fim_segundos': float(fim_segundos),
            'duracao_segundos': duracao,
            'titulo': titulo_short,
            'indice_sugestao': indice_sugestao,
            'tamanho_bytes': os.path.getsize(output_path)
        }
        shorts_baixados.append(short_info)
        
        video_salvo['shorts_baixados'] = shorts_baixados
        dados_path = persistencia.obter_caminho_video(video_id)
        with open(dados_path, 'w', encoding='utf-8') as f:
            json.dump(video_salvo, f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'caminho_arquivo': output_path,
            'video_id': video_id,
            'cache': False
        })

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout ao processar short'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@shorts_bp.route('/shorts/listar/<video_id>', methods=['GET'])
def listar_shorts(video_id):
    """Lista todos os shorts baixados de um vídeo"""
    try:
        video_salvo = persistencia.obter_video_por_id(video_id)
        if not video_salvo:
            return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404

        shorts_baixados = video_salvo.get('shorts_baixados', [])
        
        # Verifica quais arquivos ainda existem
        shorts_validos = []
        for short in shorts_baixados:
            caminho = short.get('caminho_arquivo')
            if caminho and os.path.exists(caminho):
                shorts_validos.append(short)

        return jsonify({
            'success': True,
            'shorts': shorts_validos,
            'total': len(shorts_validos)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _obter_comando_ytdlp():
    """Retorna o comando base para executar o yt-dlp."""
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    if shutil.which("python"):
        return ["python", "-m", "yt_dlp"]
    if shutil.which("python3"):
        return ["python3", "-m", "yt_dlp"]
    return None


def _ajustar_intervalo_descarga(inicio, fim, duracao_video=None):
    """Garante que o intervalo esteja entre 40s e 3 minutos."""
    inicio = max(0.0, float(inicio))
    fim = max(inicio, float(fim))
    duracao = fim - inicio

    if duracao < MIN_SHORT_DURATION:
        fim = inicio + MIN_SHORT_DURATION
        duracao = MIN_SHORT_DURATION

    if duracao > MAX_SHORT_DURATION:
        fim = inicio + MAX_SHORT_DURATION
        duracao = MAX_SHORT_DURATION

    if duracao_video:
        duracao_video = float(duracao_video)
        if duracao_video < MIN_SHORT_DURATION:
            return 0.0, float(duracao_video), float(duracao_video)
        if fim > duracao_video:
            fim = duracao_video
            inicio = max(0.0, fim - duracao)
            if fim - inicio < MIN_SHORT_DURATION:
                inicio = max(0.0, fim - MIN_SHORT_DURATION)
                duracao = fim - inicio

    return inicio, fim, duracao

