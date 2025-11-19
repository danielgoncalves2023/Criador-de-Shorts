"""
Rotas de Áudio - Download de áudio de vídeos do YouTube
"""

from flask import Blueprint, request, jsonify
import os
import subprocess
import sys
import shutil

from urllib.parse import urlparse, parse_qs

# Adiciona o diretório raiz ao path para importar utils
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
sys.path.insert(0, BASE_DIR)
from utils.persistencia import persistencia

audio_bp = Blueprint('audio', __name__)

def _extrair_video_id(url: str):
    """Extrai o ID do vídeo de uma URL do YouTube"""
    try:
        parsed = urlparse(url)
        if 'youtu.be' in parsed.netloc:
            return parsed.path.lstrip('/')
        elif 'youtube.com' in parsed.netloc:
            return parse_qs(parsed.query).get("v", [None])[0]
    except:
        pass
    return None

@audio_bp.route('/audio/download', methods=['POST'])
def baixar_audio():
    """Faz o download do áudio de um vídeo do YouTube"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
            
        url = data.get('url')
        video_id = data.get('video_id')

        # Se não tem URL mas tem video_id, tenta buscar a URL do vídeo salvo
        if not url and video_id:
            video_salvo = persistencia.obter_video_por_id(video_id)
            if video_salvo:
                url = video_salvo.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL do vídeo não fornecida'}), 400

        # Extrai ID do vídeo se não foi fornecido
        if not video_id:
            video_id = _extrair_video_id(url)
        
        if not video_id:
            return jsonify({'success': False, 'error': 'ID do vídeo não encontrado'}), 400

        # Verifica se o áudio já foi baixado
        video_salvo = persistencia.obter_video(url)
        if video_salvo and 'audio' in video_salvo:
            audio_data = video_salvo['audio']
            if audio_data.get('caminho_arquivo') and os.path.exists(audio_data['caminho_arquivo']):
                return jsonify({
                    'success': True, 
                    'audio_path': audio_data['caminho_arquivo'],
                    'video_id': video_id,
                    'cache': True
                })

        # Define caminho de saída
        output_dir = os.path.join(UPLOAD_DIR, "audios")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{video_id}.mp3")

        # Se o arquivo já existe, retorna ele
        if os.path.exists(output_path):
            audio_data = {
                'caminho_arquivo': output_path,
                'tamanho_bytes': os.path.getsize(output_path)
            }
            persistencia.atualizar_etapa(video_id, 'audio', audio_data)
            return jsonify({
                'success': True, 
                'audio_path': output_path,
                'video_id': video_id,
                'cache': True
            })

        # Comando yt-dlp para extrair áudio
        # Tenta usar python -m yt_dlp primeiro (funciona quando instalado via pip)
        # Se não funcionar, tenta yt-dlp diretamente
        
        # Verifica qual comando está disponível
        comando_base = None
        if shutil.which("yt-dlp"):
            comando_base = "yt-dlp"
        elif shutil.which("python"):
            # Tenta python -m yt_dlp
            comando_base = ["python", "-m", "yt_dlp"]
        elif shutil.which("python3"):
            comando_base = ["python3", "-m", "yt_dlp"]
        else:
            return jsonify({
                'success': False, 
                'error': 'yt-dlp não encontrado. Instale com: pip install yt-dlp'
            }), 500
        
        # Monta o comando
        if isinstance(comando_base, list):
            comando = comando_base + [
                "-f", "bestaudio/best",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--output", output_path,
                "--quiet",
                "--no-warnings",
                url
            ]
        else:
            comando = [
                comando_base,
                "-f", "bestaudio/best",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--output", output_path,
                "--quiet",
                "--no-warnings",
                url
            ]

        try:
            resultado = subprocess.run(comando, capture_output=True, text=True, timeout=600, shell=False)
        except FileNotFoundError:
            # Se yt-dlp não foi encontrado, tenta usar o módulo Python diretamente
            try:
                import yt_dlp
                # Remove .mp3 do caminho para o yt_dlp adicionar a extensão correta
                output_base = output_path.replace('.mp3', '')
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '0',
                    }],
                    'outtmpl': output_base + '.%(ext)s',
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Verifica se o arquivo foi criado
                # O yt_dlp pode criar com extensão .mp3 ou outra
                arquivo_encontrado = None
                if os.path.exists(output_path):
                    arquivo_encontrado = output_path
                else:
                    # Procura arquivo com extensão diferente na mesma pasta
                    base_name = os.path.splitext(output_path)[0]
                    for ext in ['.mp3', '.m4a', '.webm', '.opus', '.ogg']:
                        alt_path = base_name + ext
                        if os.path.exists(alt_path):
                            arquivo_encontrado = alt_path
                            # Se não for .mp3, renomeia
                            if ext != '.mp3':
                                shutil.move(alt_path, output_path)
                                arquivo_encontrado = output_path
                            break
                
                if not arquivo_encontrado or not os.path.exists(arquivo_encontrado):
                    return jsonify({
                        'success': False, 
                        'error': 'Arquivo de áudio não foi gerado após o download. Verifique se o ffmpeg está instalado.'
                    }), 500
                
                # Se chegou aqui, o download foi bem-sucedido
                resultado = type('obj', (object,), {'returncode': 0, 'stderr': '', 'stdout': ''})()
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f'Erro ao baixar áudio usando yt_dlp Python: {error_details}')
                return jsonify({
                    'success': False, 
                    'error': f'Erro ao baixar áudio: {str(e)}. Certifique-se de que o ffmpeg está instalado.'
                }), 500
        
        if resultado.returncode != 0:
            print('YT-DLP STDERR:', resultado.stderr)
            print('YT-DLP STDOUT:', resultado.stdout)
            return jsonify({
                'success': False, 
                'error': resultado.stderr or resultado.stdout or 'Erro desconhecido ao baixar áudio'
            }), 500
        
        if not os.path.exists(output_path):
            return jsonify({'success': False, 'error': 'Arquivo de áudio não foi gerado.'}), 500
        
        # Salva informações do áudio
        audio_data = {
            'caminho_arquivo': output_path,
            'tamanho_bytes': os.path.getsize(output_path)
        }
        persistencia.atualizar_etapa(video_id, 'audio', audio_data)
        
        return jsonify({
            'success': True, 
            'audio_path': output_path,
            'video_id': video_id,
            'cache': False
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout ao baixar áudio. O vídeo pode ser muito longo.'}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'error': f'Erro ao baixar áudio: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
