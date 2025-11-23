"""
Rotas de Análise - Utiliza Ollama com estratégia de Chunking (Janela Deslizante)
Focado em cortes virais evangélicos de alta retenção.
"""

print("[DEBUG] >>> Carregando módulo analise.py OTIMIZADO <<<")

from flask import Blueprint, request, jsonify
import ollama
import os
import sys
import json
import math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_SHORT_DURATION = 50  # Aumentado para garantir conteúdo
MAX_SHORT_DURATION = 120 # Foco em 60-90s (Sweet spot do YouTube/TikTok)

sys.path.insert(0, BASE_DIR)
from utils.persistencia import persistencia

analise_bp = Blueprint('analise', __name__)

# Prompt focado na engenharia reversa de vídeos virais do meio Gospel
PROMPT_ANALISE_GOSPEL = """
Você é um editor sênior de canais cristãos virais (ex: Douglas Gonçalves, Deive Leonardo). Sua especialidade é identificar momentos de "kairós" (tempo oportuno) em pregações.

ATENÇÃO: Analise este TRECHO da pregação (não é o vídeo todo).
Identifique APENAS os momentos onde há um pico emocional, uma revelação bíblica profunda ou uma história ilustrativa (storytelling) que funcione sozinha.

CRITÉRIOS PARA UM CORTE PERFEITO:
1. **Início Impactante (Hook):** O trecho NÃO pode começar com "E...", "Então...", "Mas...". Deve começar com uma afirmação forte ou uma pergunta.
2. **Meio (Retenção):** Deve haver um desenvolvimento da ideia ou uma tensão narrativa.
3. **Fim (Punchline):** O corte deve terminar logo após uma frase de impacto ou conclusão do raciocínio. NÃO corte no meio da respiração.

Retorne um JSON com 2 a 3 sugestões DESTE TRECHO ESPECÍFICO:
{
  "sugestoes": [
    {
      "titulo": "Título apelativo (ex: A Verdade que Ninguém te Conta sobre Ansiedade)",
      "citacao_inicio": "Texto exato das primeiras 5 palavras onde começa o corte",
      "citacao_fim": "Texto exato das últimas 5 palavras onde termina o corte",
      "resumo": "Explicação teológica breve",
      "gatilho_viral": "Identificação / Medo / Esperança / Confronto",
      "score": 0 a 100 (Quão forte é esse corte?)
    }
  ]
}

Transcrição do TRECHO:
{transcricao_trecho}
"""

def encontrar_timestamps_por_texto(transcricao_completa_objs, texto_inicio, texto_fim):
    """
    Tenta localizar os segundos exatos buscando o texto dentro dos segmentos do Whisper.
    Isso corrige a alucinação de tempo da IA.
    """
    inicio_sec = None
    fim_sec = None
    
    # Normalização simples para busca
    texto_inicio_norm = texto_inicio.lower().replace("...", "").strip()
    texto_fim_norm = texto_fim.lower().replace("...", "").strip()
    
    # Busca Início
    for seg in transcricao_completa_objs:
        if texto_inicio_norm in seg['texto'].lower():
            inicio_sec = seg['inicio']
            break
            
    # Busca Fim (começando a busca de onde achou o início ou do começo)
    start_search_index = 0
    if inicio_sec:
        # Otimização: buscar fim apenas após o início
        pass 

    for seg in transcricao_completa_objs:
        if seg['inicio'] >= (inicio_sec if inicio_sec else 0):
            if texto_fim_norm in seg['texto'].lower():
                fim_sec = seg['fim']
                # Se achou, paramos. Queremos o primeiro match após o início
                break
    
    return inicio_sec, fim_sec

@analise_bp.route('/analise/sugestoes', methods=['POST'])
def gerar_sugestoes():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200
    
    print(f"\n[ANALISE] POST recebido")
    
    try:
        data = request.json
        video_id = data.get('video_id')
        url = data.get('url')
        transcricao_texto = data.get('transcricao_texto') # Texto corrido
        reprocessar = bool(data.get('reprocessar'))

        # Recuperação dos dados
        if url:
            video_salvo = persistencia.obter_video(url)
            video_id = video_salvo.get('video_id') if video_salvo else None
        else:
            video_salvo = persistencia.obter_video_por_id(video_id)

        if not video_salvo:
            return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404

        # Se já existe e não é reprocessamento, retorna cache
        if not reprocessar and 'analise' in video_salvo and video_salvo['analise'].get('sugestoes'):
            return jsonify({
                'success': True,
                'sugestoes': video_salvo['analise']['sugestoes'],
                'video_id': video_id,
                'cache': True
            })

        # Precisamos dos segmentos detalhados (com timestamp) e não só do texto corrido
        segmentos_transcricao = video_salvo.get('transcricao', {}).get('segmentos', [])
        if not segmentos_transcricao:
            return jsonify({'success': False, 'error': 'Segmentos da transcrição não encontrados. Refaça a transcrição.'}), 400

        # ==================================================================
        # ESTRATÉGIA DE CHUNKING (JANELA DESLIZANTE)
        # ==================================================================
        
        duracao_total = video_salvo.get('info_video', {}).get('duracao_segundos', 0)
        
        # Configuração dos blocos
        TAMANHO_BLOCO_MINUTOS = 10 # Analisa de 10 em 10 minutos
        OVERLAP_MINUTOS = 1        # Volta 1 minuto para não perder contexto
        
        tamanho_bloco_sec = TAMANHO_BLOCO_MINUTOS * 60
        overlap_sec = OVERLAP_MINUTOS * 60
        
        cursor = 0
        todas_sugestoes_brutas = []
        
        print(f"[ANALISE] Iniciando análise por blocos. Duração total: {duracao_total}s")
        
        modelo_ollama = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
        
        while cursor < duracao_total:
            fim_bloco = min(cursor + tamanho_bloco_sec, duracao_total)
            print(f"[ANALISE] Processando bloco: {int(cursor)}s até {int(fim_bloco)}s")
            
            # Filtra segmentos do bloco atual
            texto_bloco = ""
            for seg in segmentos_transcricao:
                if seg['inicio'] >= cursor and seg['fim'] <= fim_bloco:
                    texto_bloco += f"{seg['texto']} "
            
            if len(texto_bloco) > 200: # Só analisa se tiver conteúdo suficiente
                prompt = PROMPT_ANALISE_GOSPEL.replace("{transcricao_trecho}", texto_bloco)
                
                try:
                    resposta = ollama.chat(
                        model=modelo_ollama,
                        messages=[
                            {'role': 'system', 'content': 'Você é um especialista em viralização de vídeos cristãos. Retorne APENAS JSON válido.'},
                            {'role': 'user', 'content': prompt}
                        ],
                        options={'temperature': 0.7} # Criatividade controlada
                    )
                    
                    conteudo = resposta['message']['content'].strip()
                    # Limpeza básica de Markdown
                    if conteudo.startswith('```'):
                        conteudo = conteudo.split('\n', 1)[1].rsplit('\n', 1)[0]
                    
                    # Extração de JSON (robusta)
                    import re
                    json_match = re.search(r'\{.*\}', conteudo, re.DOTALL)
                    if json_match:
                        resultado = json.loads(json_match.group())
                        sugestoes_bloco = resultado.get('sugestoes', [])
                        
                        # Adiciona offset temporal aproximado se a IA não devolver timestamp (fallback)
                        for s in sugestoes_bloco:
                            s['_bloco_inicio'] = cursor 
                        
                        todas_sugestoes_brutas.extend(sugestoes_bloco)
                        print(f"   -> {len(sugestoes_bloco)} sugestões encontradas neste bloco.")
                    
                except Exception as e:
                    print(f"[ERRO] Falha ao processar bloco {cursor}: {str(e)}")
            
            # Avança o cursor (menos o overlap)
            cursor += (tamanho_bloco_sec - overlap_sec)

       # ==================================================================
        # POS-PROCESSAMENTO E REFINAMENTO DE TEMPOS (CORRIGIDO)
        # ==================================================================
        print("[ANALISE] Refinando tempos e validando cortes...")
        
        sugestoes_finais = []
        
        # Ordena por score (se houver) para pegar os melhores
        todas_sugestoes_brutas.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Limita a quantidade total baseada na duração do vídeo
        max_shorts = max(5, int(duracao_total / 300))
        top_sugestoes = todas_sugestoes_brutas[:max_shorts]

        for sug in top_sugestoes:
            # Tenta achar o timestamp exato pelo texto citado pela IA
            txt_ini = sug.get('citacao_inicio', '')
            txt_fim = sug.get('citacao_fim', '')
            
            inicio_real, fim_real = encontrar_timestamps_por_texto(segmentos_transcricao, txt_ini, txt_fim)
            
            # CORREÇÃO AQUI: Verifica se tanto o início quanto o fim foram encontrados
            if inicio_real is None or fim_real is None:
                print(f"   [SKIP] Sugestão ignorada (texto não encontrado na transcrição): {sug.get('titulo')}")
                continue

            # Padding de segurança (Áudio Breathing Room)
            inicio_real = max(0, float(inicio_real) - 1.5)
            
            # Garante que fim_real é float antes de somar
            fim_real = float(fim_real)
            fim_real = min(float(duracao_total), fim_real + 1.5)
            
            # Validação de Duração
            duracao = fim_real - inicio_real
            
            # Se for muito curto, tentamos expandir para a próxima frase (contexto)
            if duracao < MIN_SHORT_DURATION:
                fim_real += (MIN_SHORT_DURATION - duracao)
                # Garante que não passou do final do vídeo
                fim_real = min(float(duracao_total), fim_real)
                duracao = fim_real - inicio_real
            
            # Se for muito longo, cortamos
            if duracao > MAX_SHORT_DURATION:
                fim_real = inicio_real + MAX_SHORT_DURATION
                duracao = MAX_SHORT_DURATION

            sugestoes_finais.append({
                'titulo': sug.get('titulo', 'Short Viral'),
                'inicio_segundos': round(inicio_real, 2),
                'fim_segundos': round(fim_real, 2),
                'duracao_segundos': round(duracao, 2),
                'descricao': sug.get('resumo', ''),
                'potencial_viral': sug.get('gatilho_viral', 'Impacto Emocional'),
                'hook': txt_ini,
                'tags': ["#gospel", "#pregação", "#fé", "#motivação", "#shorts"]
            })

        # Ordena cronologicamente para facilitar a edição
        sugestoes_finais.sort(key=lambda x: x['inicio_segundos'])

        if not sugestoes_finais:
             return jsonify({
                'success': False,
                'error': 'A IA analisou os blocos mas não conseguiu extrair cortes com qualidade suficiente.'
            }), 500

        analise_data = {
            'sugestoes': sugestoes_finais,
            'total_sugestoes': len(sugestoes_finais),
            'modelo_ia': modelo_ollama,
            'metodo': 'chunking_v2'
        }
        persistencia.atualizar_etapa(video_id, 'analise', analise_data)

        return jsonify({
            'success': True,
            'sugestoes': sugestoes_finais,
            'video_id': video_id,
            'cache': False
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@analise_bp.route('/analise/atualizar-intervalo', methods=['POST'])
def atualizar_intervalo():
    """Atualiza o intervalo manualmente e recalcula a duração"""
    try:
        data = request.json or {}
        video_id = data.get('video_id')
        indice = data.get('indice')
        inicio_segundos = float(data.get('inicio_segundos'))
        fim_segundos = float(data.get('fim_segundos'))

        video_salvo = persistencia.obter_video_por_id(video_id)
        if not video_salvo:
            return jsonify({'success': False, 'error': 'Vídeo não encontrado'}), 404

        analise = video_salvo.get('analise', {})
        sugestoes = analise.get('sugestoes', [])

        if 0 <= indice < len(sugestoes):
            sugestoes[indice]['inicio_segundos'] = inicio_segundos
            sugestoes[indice]['fim_segundos'] = fim_segundos
            sugestoes[indice]['duracao_segundos'] = fim_segundos - inicio_segundos
            
            persistencia.atualizar_etapa(video_id, 'analise', analise)
            
            return jsonify({'success': True, 'sugestao': sugestoes[indice]})
        
        return jsonify({'success': False, 'error': 'Índice inválido'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500