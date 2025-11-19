"""
Rotas de Análise - Utiliza Ollama para analisar transcrições e gerar sugestões de shorts
"""

print("[DEBUG] >>> Carregando módulo analise.py <<<")

from flask import Blueprint, request, jsonify
import ollama
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_SHORT_DURATION = 40  # segundos
MAX_SHORT_DURATION = 180  # 3 minutos

# Adiciona o diretório raiz ao path para importar utils
sys.path.insert(0, BASE_DIR)
from utils.persistencia import persistencia

analise_bp = Blueprint('analise', __name__)

PROMPT_ANALISE = """Você é um especialista cristão em criação de vídeos virais de shorts para YouTube e TikTok.

Analise a transcrição do vídeo abaixo e identifique os melhores momentos para criar shorts virais. 

Para cada sugestão de short, forneça:
1. Título impactante e chamativo (máximo 60 caracteres)
2. Descrição do momento (início e fim em segundos)
3. Por que esse momento tem potencial viral
4. Sugestão de hook (primeira frase para prender atenção)
5. Tags sugeridas

Transcrição do vídeo:
{transcricao}

Retorne APENAS um JSON válido com o seguinte formato:
{{
  "sugestoes": [
    {{
      "titulo": "Título do short",
      "inicio_segundos": 120.5,
      "fim_segundos": 150.3,
      "duracao_segundos": 29.8,
      "descricao": "Descrição do momento",
      "potencial_viral": "Por que tem potencial viral",
      "hook": "Primeira frase impactante",
      "tags": ["tag1", "tag2", "tag3"]
    }}
  ]
}}

Gere entre 3 e 8 sugestões de shorts potenciais. Foque em momentos com:
- Emoção alta
- Lições práticas
- Momentos de reflexão
- Histórias impactantes
- Ensino claro e direto
"""

@analise_bp.route('/analise/sugestoes', methods=['POST'])
def gerar_sugestoes():
    """Analisa a transcrição e gera sugestões de shorts usando Ollama"""
    
    # Responde ao preflight do CORS (SEM espaço extra antes do #)
    if request.method == 'OPTIONS':
        print("[ANALISE] Respondendo ao preflight OPTIONS")
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200
    
    print(f"\n[ANALISE] POST recebido - video_id: {request.json.get('video_id')}")
    
    try:
        data = request.json
        video_id = data.get('video_id')
        url = data.get('url')
        transcricao_texto = data.get('transcricao_texto')
        reprocessar = bool(data.get('reprocessar'))

        print("Recebido request para /sugestoes com video_id:", video_id, "url:", url, "reprocessar:", reprocessar)
        if not video_id and not url:
            return jsonify({'success': False, 'error': 'ID do vídeo ou URL não fornecidos'}), 400

        print("Obtendo dados do vídeo...")
        # Obtém dados do vídeo
        if url:
            video_salvo = persistencia.obter_video(url)
            if not video_salvo:
                return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404
            video_id = video_salvo.get('video_id')
        else:
            # Busca por video_id
            video_salvo = persistencia.obter_video_por_id(video_id)

        if not video_salvo:
            return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404

        print("Verificando análise salva...")
        # Verifica se já existe análise salva
        if not reprocessar and 'analise' in video_salvo and video_salvo['analise'].get('sugestoes'):
            return jsonify({
                'success': True,
                'sugestoes': video_salvo['analise']['sugestoes'],
                'video_id': video_id,
                'cache': True
            })

        print("Preparando transcrição...")
        # Obtém transcrição
        if not transcricao_texto:
            if 'transcricao' in video_salvo:
                transcricao_texto = video_salvo['transcricao'].get('texto')
            else:
                return jsonify({
                    'success': False, 
                    'error': 'Transcrição não encontrada. Transcreva o áudio primeiro.'
                }), 400

        if not transcricao_texto or len(transcricao_texto.strip()) < 50:
            return jsonify({
                'success': False, 
                'error': 'Transcrição muito curta ou vazia'
            }), 400

        # Prepara prompt
        prompt = PROMPT_ANALISE.format(transcricao=transcricao_texto)

        print("Chamando Ollama para análise...")
        # Chama Ollama
        try:
            # Usa o modelo llama3.2:3b (versão 3B do llama3.2)
            modelo_ollama = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
            resposta = ollama.chat(
                model=modelo_ollama,
                messages=[
                    {
                        'role': 'system',
                        'content': 'Você é um especialista em análise de conteúdo para criação de shorts virais. Sempre retorne apenas JSON válido, sem markdown ou formatação adicional.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            conteudo = resposta['message']['content'].strip()
            
            # Remove markdown code blocks se existirem
            if conteudo.startswith('```'):
                linhas = conteudo.split('\n')
                conteudo = '\n'.join(linhas[1:-1]) if len(linhas) > 2 else conteudo
            
            print("Resposta da IA:", conteudo)
            # Tenta parsear JSON
            try:
                resultado = json.loads(conteudo)
            except json.JSONDecodeError:
                # Tenta extrair JSON do texto
                import re
                json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
                if json_match:
                    resultado = json.loads(json_match.group())
                else:
                    raise ValueError("Não foi possível extrair JSON da resposta")

            sugestoes = resultado.get('sugestoes', [])
            
            if not sugestoes:
                return jsonify({
                    'success': False,
                    'error': 'Nenhuma sugestão foi gerada pela IA'
                }), 500
            duracao_video = video_salvo.get('info_video', {}).get('duracao_segundos')

            # Valida e formata sugestões
            sugestoes_validas = []
            for sug in sugestoes:
                if all(k in sug for k in ['titulo', 'inicio_segundos', 'fim_segundos']):
                    inicio = float(sug.get('inicio_segundos', 0))
                    fim = float(sug.get('fim_segundos', 0))
                    inicio, fim, duracao = _ajustar_intervalo(inicio, fim, duracao_video)
                    sugestoes_validas.append({
                        'titulo': sug.get('titulo', 'Sem título'),
                        'inicio_segundos': inicio,
                        'fim_segundos': fim,
                        'duracao_segundos': duracao,
                        'descricao': sug.get('descricao', ''),
                        'potencial_viral': sug.get('potencial_viral', ''),
                        'hook': sug.get('hook', ''),
                        'tags': sug.get('tags', [])
                    })

            if not sugestoes_validas:
                return jsonify({
                    'success': False,
                    'error': 'Nenhuma sugestão válida foi gerada'
                }), 500

            print("Sugestões geradas com sucesso.")
            # Salva análise
            analise_data = {
                'sugestoes': sugestoes_validas,
                'total_sugestoes': len(sugestoes_validas),
                'modelo_ia': modelo_ollama
            }
            persistencia.atualizar_etapa(video_id, 'analise', analise_data)

            return jsonify({
                'success': True,
                'sugestoes': sugestoes_validas,
                'video_id': video_id,
                'cache': False
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Erro ao chamar Ollama: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _ajustar_intervalo(inicio, fim, duracao_video=None):
    """Normaliza o intervalo dentro das regras de duração."""
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
            raise ValueError('A duração do vídeo é menor que o mínimo exigido para shorts (40s)')

        if fim > duracao_video:
            fim = duracao_video
            inicio = max(0.0, fim - duracao)
            # Se ainda assim ficar menor que o mínimo (por exemplo, o vídeo termina logo depois)
            if fim - inicio < MIN_SHORT_DURATION:
                inicio = max(0.0, fim - MIN_SHORT_DURATION)
                duracao = fim - inicio

    return inicio, fim, duracao

@analise_bp.route('/analise/atualizar-intervalo', methods=['POST'])
def atualizar_intervalo():
    """Atualiza o intervalo de uma sugestão específica."""
    try:
        data = request.json or {}
        video_id = data.get('video_id')
        indice = data.get('indice')
        inicio_segundos = data.get('inicio_segundos')
        fim_segundos = data.get('fim_segundos')

        if video_id is None or indice is None:
            return jsonify({'success': False, 'error': 'Video ID e índice são obrigatórios'}), 400

        try:
            indice = int(indice)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Índice inválido'}), 400

        if inicio_segundos is None or fim_segundos is None:
            return jsonify({'success': False, 'error': 'Tempos de início e fim são obrigatórios'}), 400

        video_salvo = persistencia.obter_video_por_id(video_id)
        if not video_salvo:
            return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404

        analise_salva = video_salvo.get('analise', {})
        sugestoes = analise_salva.get('sugestoes', [])

        if indice < 0 or indice >= len(sugestoes):
            return jsonify({'success': False, 'error': 'Sugestão não encontrada'}), 404

        duracao_video = video_salvo.get('info_video', {}).get('duracao_segundos')
        inicio_norm, fim_norm, duracao_norm = _ajustar_intervalo(
            inicio_segundos,
            fim_segundos,
            duracao_video
        )

        sugestoes[indice] = {
            **sugestoes[indice],
            'inicio_segundos': inicio_norm,
            'fim_segundos': fim_norm,
            'duracao_segundos': duracao_norm
        }

        analise_salva['sugestoes'] = sugestoes
        video_salvo['analise'] = analise_salva

        dados_path = persistencia.obter_caminho_video(video_id)
        with open(dados_path, 'w', encoding='utf-8') as f:
            json.dump(video_salvo, f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'sugestao': sugestoes[indice],
            'indice': indice
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

