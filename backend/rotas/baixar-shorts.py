"""
Rotas de Download de Shorts - Baixa os shorts sugeridos pela IA
"""

from flask import Blueprint, request, jsonify
import os
import subprocess
import sys
import json
import shutil
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SHORTS_DIR = os.path.join(UPLOAD_DIR, "shorts")
TEMP_VIDEO_TEMPLATE = "{video_id}_temp.mp4"
MIN_SHORT_DURATION = 40
MAX_SHORT_DURATION = 180

sys.path.insert(0, BASE_DIR)
from utils.persistencia import persistencia

shorts_bp = Blueprint('shorts', __name__)

def _obter_comando_ytdlp():
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    if shutil.which("python"):
        return ["python", "-m", "yt_dlp"]
    if shutil.which("python3"):
        return ["python3", "-m", "yt_dlp"]
    return None

def _ajustar_intervalo_descarga(inicio, fim, duracao_video=None):
    """Garante o intervalo mínimo de 40s e máximo de 3min."""
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
            return 0.0, duracao_video, duracao_video

        if fim > duracao_video:
            fim = duracao_video
            inicio = max(0.0, fim - duracao)
            if fim - inicio < MIN_SHORT_DURATION:
                inicio = max(0.0, fim - MIN_SHORT_DURATION)
                duracao = fim - inicio

    return inicio, fim, duracao

# ------------------------------
# ROTA PRINCIPAL — DOWNLOAD SHORT
# ------------------------------
@shorts_bp.route('/shorts/baixar', methods=['POST'])
def baixar_short():
    try:
        data = request.json
        video_id = data.get('video_id')
        url = data.get('url')
        inicio_segundos = float(data.get('inicio_segundos', 0))
        fim_segundos = float(data.get('fim_segundos', 0))
        titulo_short = data.get('titulo', 'short')
        indice_sugestao = data.get('indice_sugestao', 0)

        if not video_id and not url:
            return jsonify({'success': False, 'error': 'ID do vídeo ou URL não fornecidos'}), 400

        if inicio_segundos is None or fim_segundos is None:
            return jsonify({'success': False, 'error': 'Tempos não fornecidos'}), 400

        # Buscar dados persistidos
        if url:
            video_salvo = persistencia.obter_video(url)
            if not video_salvo:
                return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404
            video_id = video_salvo["video_id"]
            url_video = url
        else:
            video_salvo = persistencia.obter_video_por_id(video_id)
            if not video_salvo:
                return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404
            url_video = video_salvo["url"]

        duracao_video = video_salvo.get("info_video", {}).get("duracao_segundos")
        inicio_segundos, fim_segundos, duracao = _ajustar_intervalo_descarga(
            inicio_segundos, fim_segundos, duracao_video
        )

        os.makedirs(SHORTS_DIR, exist_ok=True)

        nome_arquivo = f"{video_id}_short_{indice_sugestao}_{int(inicio_segundos)}s.mp4"
        output_path = os.path.join(SHORTS_DIR, nome_arquivo)

        # ------------------------------
        # Download do vídeo FULL (se não existe)
        # ------------------------------
        temp_path = os.path.join(SHORTS_DIR, TEMP_VIDEO_TEMPLATE.format(video_id=video_id))
        comando_base = _obter_comando_ytdlp()

        if not comando_base:
            return jsonify({'success': False, 'error': 'yt-dlp não encontrado'}), 500

        if not os.path.exists(temp_path):
            resultado = subprocess.run(
                comando_base + [
                    "-f", "best[height<=1080]",
                    "--output", temp_path,
                    "--quiet",
                    "--no-warnings",
                    url_video
                ],
                capture_output=True, text=True, timeout=600
            )
            if resultado.returncode != 0:
                return jsonify({'success': False, 'error': 'Erro ao baixar vídeo'}), 500

        # ------------------------------
        # Criar EVENTOS DE LEGENDAS (por FRASE)
        # ------------------------------
        segmentos = video_salvo.get("transcricao", {}).get("segmentos", [])
        eventos = []

        for seg in segmentos:
            if seg["fim"] >= inicio_segundos and seg["inicio"] <= fim_segundos:

                inicio_seg = float(seg["inicio"])
                fim_seg = float(seg["fim"])
                frase = seg["texto"].strip()
                if not frase:
                    continue

                start_rel = max(inicio_seg - inicio_segundos, 0)
                end_rel = min(fim_seg - inicio_segundos, duracao)

                frase = (
                    frase.replace(":", "\\:")
                         .replace("'", "\\'")
                         .replace('"', '\\"')
                )

                eventos.append({
                    "text": frase,
                    "start": start_rel,
                    "end": end_rel
                })

        # ------------------------------
        # FILTRO 9:16 + LEGENDAS PROFISSIONAIS
        # ------------------------------
        vertical_filter = "scale=-2:1920,crop=1080:1920"

        draws = []

        # LEGENDA LIMPA (SEM FUNDO) — +70px e com fade
        for ev in eventos:
            draws.append(
                "drawtext=text='{}':"
                "fontcolor=white:"
                "fontsize=60:"
                "line_spacing=10:"
                "x=(w-text_w)/2:"
                "y=h-350:"  # posição ajustada
                "alpha='if(lt(t,{:.3f}), (t-{:.3f})/0.25, if(lt(t,{:.3f}), 1, ({}-t)/0.25))'"
                .format(
                    ev["text"],
                    ev["start"], ev["start"],
                    ev["end"], ev["end"]
                )
            )

        # ------------------------------
        # MARCA D'ÁGUA ACIMA (+ opacidade baixa)
        # ------------------------------
        watermark = (
            "drawtext=text='@CortesdoReinodeDeus':"
            "fontcolor=white@0.35:"
            "fontsize=42:"
            "x=(w-text_w)/2:"
            "y=h-470"  # bem acima da legenda
        )
        draws.append(watermark)

        filtro_com_texto = vertical_filter + "," + ",".join(draws)

        # ------------------------------
        # FFmpeg FINAL
        # ------------------------------
        comando_cortar = [
            "ffmpeg",
            "-ss", str(inicio_segundos),
            "-t", str(duracao),
            "-i", temp_path,
            "-vf", filtro_com_texto,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-y",
            output_path
        ]

        resultado = subprocess.run(comando_cortar, capture_output=True, text=True, timeout=600)
        if resultado.returncode != 0:
            return jsonify({'success': False, 'error': resultado.stderr}), 500

        # ------------------------------
        # SALVAR METADADOS
        # ------------------------------
        shorts_baixados = video_salvo.get("shorts_baixados", [])
        shorts_baixados.append({
            "caminho_arquivo": output_path,
            "inicio_segundos": inicio_segundos,
            "fim_segundos": fim_segundos,
            "duracao_segundos": duracao,
            "titulo": titulo_short,
            "indice_sugestao": indice_sugestao,
            "tamanho_bytes": os.path.getsize(output_path)
        })

        video_salvo["shorts_baixados"] = shorts_baixados
        path_json = persistencia.obter_caminho_video(video_id)

        with open(path_json, "w", encoding="utf-8") as f:
            json.dump(video_salvo, f, ensure_ascii=False, indent=2)

        return jsonify({
            "success": True,
            "video_id": video_id,
            "caminho_arquivo": output_path
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ------------------------------
# LISTAGEM
# ------------------------------
@shorts_bp.route('/shorts/listar/<video_id>', methods=['GET'])
def listar_shorts(video_id):
    try:
        video_salvo = persistencia.obter_video_por_id(video_id)
        if not video_salvo:
            return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404

        shorts_baixados = video_salvo.get("shorts_baixados", [])
        shorts_validos = [s for s in shorts_baixados if os.path.exists(s["caminho_arquivo"])]

        return jsonify({
            "success": True,
            "shorts": shorts_validos,
            "total": len(shorts_validos)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500