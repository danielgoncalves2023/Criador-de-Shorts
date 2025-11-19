# Criador de Shorts - Gerador de Shorts Virais com IA

Sistema completo para transformar vídeos do YouTube em shorts virais usando inteligência artificial. O sistema analisa vídeos, transcreve o áudio, identifica momentos virais e gera sugestões de shorts otimizados.

## 🚀 Funcionalidades

- **Busca de Informações**: Extrai informações completas de vídeos do YouTube
- **Download de Áudio**: Baixa o áudio do vídeo usando yt-dlp
- **Transcrição Automática**: Transcreve o áudio usando fast-whisper (Whisper otimizado)
- **Análise com IA**: Utiliza Ollama para analisar a transcrição e identificar momentos virais
- **Geração de Shorts**: Sugere múltiplos shorts potenciais com títulos, hooks e tags
- **Download de Shorts**: Baixa os shorts sugeridos automaticamente
- **Persistência Local**: Salva todo o progresso localmente para continuar de onde parou

## 📋 Pré-requisitos

### Backend (Python)
- Python 3.8+
- ffmpeg instalado no sistema
- yt-dlp instalado
- Ollama instalado e rodando (com modelo llama3.2 ou similar)

### Frontend (React/TypeScript)
- Node.js 18+
- npm ou yarn

## 🛠️ Instalação

### Backend

1. Navegue até a pasta do backend:
```bash
cd backend
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Instale o Ollama e baixe um modelo:
```bash
# Instale o Ollama de https://ollama.ai
# Depois baixe um modelo:
ollama pull llama3.2
```

5. Instale o ffmpeg:
- Windows: Baixe de https://ffmpeg.org/download.html
- Linux: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

### Frontend

1. Navegue até a pasta do frontend:
```bash
cd frontend
```

2. Instale as dependências:
```bash
npm install
```

## 🚀 Executando

### Backend

```bash
cd backend
python app.py
```

O backend estará rodando em `http://localhost:5000`

### Frontend

```bash
cd frontend
npm run dev
```

O frontend estará rodando em `http://localhost:5173` (ou outra porta do Vite)

## 📁 Estrutura do Projeto

```
Criador de Shorts/
├── backend/
│   ├── app.py                 # Aplicação Flask principal
│   ├── requirements.txt       # Dependências Python
│   ├── rotas/
│   │   ├── youtube.py         # Rotas de busca de informações
│   │   ├── baixar-audio.py    # Rotas de download de áudio
│   │   ├── transcricao.py    # Rotas de transcrição
│   │   ├── analise.py         # Rotas de análise com IA
│   │   ├── baixar-shorts.py   # Rotas de download de shorts
│   │   ├── biblioteca.py      # Rotas da biblioteca
│   │   └── rotas.py           # Registro de rotas
│   ├── utils/
│   │   └── persistencia.py    # Sistema de persistência local
│   ├── uploads/
│   │   ├── audios/            # Áudios baixados
│   │   └── shorts/            # Shorts gerados
│   └── dados/                 # Dados persistidos (JSON)
│       └── indice.json        # Índice de vídeos processados
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── PaginaInicial.tsx      # Página inicial
    │   │   ├── PaginaResultados.tsx   # Página de resultados
    │   │   └── PaginaBiblioteca.tsx    # Página de biblioteca
    │   ├── services/                  # Serviços de API
    │   ├── components/                # Componentes React
    │   └── App.tsx                    # App principal
    └── package.json
```

## 🔧 Configuração

### Variáveis de Ambiente (Opcional)

Crie um arquivo `.env` no backend para configurar:

```env
USE_CUDA=true  # Usar GPU para transcrição (se disponível)
```

### Modelo de IA

Por padrão, o sistema usa o modelo `llama3.2` do Ollama. Para usar outro modelo, edite `backend/rotas/analise.py` e altere:

```python
resposta = ollama.chat(
    model='seu-modelo-aqui',  # Altere aqui
    ...
)
```

## 📝 Uso

1. **Inserir URL**: Na página inicial, cole a URL do vídeo do YouTube
2. **Buscar Informações**: Clique em "Buscar Informações" para extrair dados do vídeo
3. **Processar Vídeo**: Clique em "Processar Vídeo e Gerar Shorts"
4. **Aguardar Processamento**: O sistema irá:
   - Baixar o áudio
   - Transcrever o áudio
   - Analisar com IA
   - Gerar sugestões de shorts
5. **Visualizar Sugestões**: Veja as sugestões de shorts na página de resultados
6. **Baixar Shorts**: Clique em "Baixar Short" para cada sugestão desejada

## 💾 Persistência

Todo o progresso é salvo localmente em:
- `backend/dados/` - Dados JSON de cada vídeo
- `backend/uploads/audios/` - Áudios baixados
- `backend/uploads/shorts/` - Shorts gerados

Se algo acontecer durante o processamento, você pode continuar de onde parou!

## 🎨 Tecnologias Utilizadas

### Backend
- Flask - Framework web
- yt-dlp - Download de vídeos do YouTube
- fast-whisper - Transcrição de áudio otimizada
- Ollama - Modelo de IA local
- ffmpeg - Processamento de vídeo

### Frontend
- React 19 - Biblioteca UI
- TypeScript - Tipagem estática
- React Router - Roteamento
- Tailwind CSS - Estilização
- Axios - Cliente HTTP
- Lucide React - Ícones

## 📄 Licença

Este projeto é de uso pessoal/educacional.

## 🤝 Contribuindo

Sinta-se à vontade para fazer fork e melhorar o projeto!

## ⚠️ Notas Importantes

- O processamento pode levar vários minutos dependendo do tamanho do vídeo
- Certifique-se de ter espaço em disco suficiente para os arquivos baixados
- O Ollama precisa estar rodando para a análise funcionar
- Vídeos muito longos podem demorar mais para processar

