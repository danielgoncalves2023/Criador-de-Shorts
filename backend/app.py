
from flask import Flask, send_from_directory
from flask_cors import CORS
from rotas.rotas import register_routes
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
CORS(app)

# Registra todas as rotas
register_routes(app)

# Rota para servir arquivos estáticos (áudios e shorts)
@app.route('/uploads/<path:filename>')
def uploads(filename):
    """Serve arquivos de upload (áudios e shorts)"""
    uploads_dir = UPLOADS_DIR
    # Extrai o diretório e o nome do arquivo
    parts = filename.split('/')
    if len(parts) > 1:
        directory = '/'.join(parts[:-1])
        file = parts[-1]
        return send_from_directory(
            os.path.join(uploads_dir, directory),
            file
        )
    return send_from_directory(uploads_dir, filename)

if __name__ == '__main__':
    # Print all registered routes for debugging
    print("\n[DEBUG] Rotas registradas no Flask:")
    for rule in app.url_map.iter_rules():
        print(f"[ROUTE] {rule.methods} {rule}")
    app.run(debug=True, port=5000)
