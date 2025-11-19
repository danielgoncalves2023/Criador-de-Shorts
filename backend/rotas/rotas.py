# rotas/rotas.py
def register_routes(app):
    """Registra todas as rotas na aplicação Flask"""
    from . import (
        youtube_bp, 
        transcricao_bp, 
        audio_bp, 
        analise_bp, 
        shorts_bp, 
        processar_bp, 
        biblioteca_bp
    )
    
    print("[DEBUG] Registrando blueprints...")
    
    blueprints = [
        (youtube_bp, '/api', 'youtube_bp'),
        (transcricao_bp, '/api', 'transcricao_bp'),
        (audio_bp, '/api', 'audio_bp'),
        (analise_bp, '/api', 'analise_bp'),  # Mudei o prefixo!
        (shorts_bp, '/api', 'shorts_bp'),
        (processar_bp, '/api', 'processar_bp'),
        (biblioteca_bp, '/api', 'biblioteca_bp'),
    ]
    
    for bp, prefix, name in blueprints:
        try:
            app.register_blueprint(bp, url_prefix=prefix)
            print(f"[DEBUG] ✓ {name} registrado em {prefix}")
        except Exception as e:
            print(f"[ERRO] ✗ Falha ao registrar {name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Lista todas as rotas
    print("\n[DEBUG] === ROTAS REGISTRADAS ===")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"[ROUTE] {methods:8} {rule.rule}")
    print("[DEBUG] ============================\n")