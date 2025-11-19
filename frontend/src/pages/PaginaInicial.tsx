import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Youtube, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import buscarInfoYoutube from "../services/buscar-info-video";
import type { InfoVideo } from "../services/buscar-info-video";

const formatarDuracao = (segundos: number) => {
  const h = Math.floor(segundos / 3600);
  const m = Math.floor((segundos % 3600) / 60);
  const s = segundos % 60;
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
};

/**
 * Componente de Página Inicial (PaginaInicial)
 * Onde o usuário insere o link do YouTube.
 */
const PaginaInicial = () => {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const [dados, setDados] = useState<InfoVideo | null>(null);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [processando, setProcessando] = useState(false);

  const handleBuscarInfoYoutube = async (urlVideo: string) => {
    setCarregando(true);
    setErro("");
    setDados(null);
    setVideoId(null);
    
    try {
      const resposta = await buscarInfoYoutube(urlVideo);
      
      if (resposta.success && resposta.video_info) {
        setDados(resposta.video_info);
        setVideoId(resposta.video_id || null);
        
        // Se já existe processamento, redireciona para resultados
        if (resposta.cache) {
          // Verifica se há processamento completo
          setTimeout(() => {
            navigate(`/resultados/${resposta.video_id}`);
          }, 1000);
        }
      } else {
        setErro(resposta.error || "Falha ao buscar informações do vídeo");
      }
    } catch (err: any) {
      setErro(err.message || "Falha na requisição");
    } finally {
      setCarregando(false);
    }
  };

  const handleProcessarVideo = () => {
    if (videoId) {
      navigate(`/resultados/${videoId}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 text-white flex flex-col items-center justify-center px-4 py-12">
      <div className="max-w-2xl w-full space-y-8">
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-3">
            <Youtube className="text-red-500 w-10 h-10" />
            <h1 className="text-4xl font-bold">Criador de Shorts</h1>
          </div>
          <p className="text-zinc-400 text-lg">
            Transforme seus vídeos do YouTube em shorts virais com IA
          </p>
        </div>

        <div className="bg-zinc-800/50 backdrop-blur-sm p-6 rounded-xl border border-zinc-700 shadow-xl space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-300">
              URL do Vídeo do YouTube
            </label>
            <input
              type="text"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && url && !carregando) {
                  handleBuscarInfoYoutube(url);
                }
              }}
              className="w-full px-4 py-3 rounded-lg bg-zinc-900/50 text-white border border-zinc-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
            />
          </div>

          <button
            onClick={() => handleBuscarInfoYoutube(url)}
            disabled={carregando || !url}
            className="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
          >
            {carregando ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                Buscando...
              </>
            ) : (
              <>
                <Search size={18} />
                Buscar Informações
              </>
            )}
          </button>

          {erro && (
            <div className="flex items-center gap-2 p-3 bg-red-900/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
              <AlertCircle size={18} />
              {erro}
            </div>
          )}
        </div>

        {dados && (
          <div className="bg-zinc-800/50 backdrop-blur-sm p-6 rounded-xl border border-zinc-700 shadow-xl space-y-4 animate-in fade-in slide-in-from-bottom-4">
            <div className="flex flex-col sm:flex-row gap-6">
              <img
                src={dados.url_thumbnail}
                alt="Thumbnail"
                className="w-full sm:w-64 h-48 sm:h-36 rounded-lg object-cover shadow-lg"
              />

              <div className="flex flex-col justify-center space-y-3 flex-1">
                <h2 className="text-xl font-bold text-white line-clamp-2">
                  {dados.titulo}
                </h2>
                <div className="space-y-1 text-sm">
                  <p className="text-zinc-400">
                    <span className="font-semibold text-white">Autor:</span>{" "}
                    {dados.autor}
                  </p>
                  <p className="text-zinc-400">
                    <span className="font-semibold text-white">Duração:</span>{" "}
                    {formatarDuracao(dados.duracao_segundos)}
                  </p>
                  {dados.visualizacoes && (
                    <p className="text-zinc-400">
                      <span className="font-semibold text-white">Visualizações:</span>{" "}
                      {dados.visualizacoes.toLocaleString('pt-BR')}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={handleProcessarVideo}
              disabled={processando || !videoId}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              {processando ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  Processando...
                </>
              ) : (
                <>
                  <CheckCircle2 size={18} />
                  Processar Vídeo e Gerar Shorts
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaginaInicial;
