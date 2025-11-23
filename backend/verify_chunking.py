import requests
import json
import time

VIDEO_ID = "--0Y6VUiztA"  # ID do vídeo de teste (substitua se necessário)
URL = "http://localhost:5000/api/analise/sugestoes"

payload = {
    "video_id": VIDEO_ID,
    "reprocessar": True  # Força o reprocessamento para testar o chunking
}

print(f"Enviando requisição para {URL} com video_id={VIDEO_ID}...")
start_time = time.time()

try:
    response = requests.post(URL, json=payload)
    end_time = time.time()
    
    print(f"Status Code: {response.status_code}")
    print(f"Tempo de resposta: {end_time - start_time:.2f} segundos")
    
    if response.status_code == 200:
        data = response.json()
        sugestoes = data.get('sugestoes', [])
        print(f"Sucesso! {len(sugestoes)} sugestões geradas.")
        for i, sug in enumerate(sugestoes):
            print(f"[{i+1}] {sug['titulo']} ({sug['duracao_segundos']}s)")
    else:
        print("Erro na requisição:")
        print(response.text)

except Exception as e:
    print(f"Erro ao conectar: {e}")
