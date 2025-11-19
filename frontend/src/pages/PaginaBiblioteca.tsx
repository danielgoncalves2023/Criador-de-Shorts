import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  BookOpen, 
  Loader2, 
  Play, 
  Calendar,
  Clock,
  Eye,
  FileVideo
} from "lucide-react";
import { api } from "../services/api";

interface VideoBiblioteca {
  video_id: string;
  url: string;
  titulo: string;
  ultima_atualizacao: string;
}

const PaginaBiblioteca = () => {
  const navigate = useNavigate();
  const [videos, setVideos] = useState<VideoBiblioteca[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    carregarBiblioteca();
  }, []);

  const carregarBiblioteca = async () => {
    setCarregando(true);
    setErro("");
    
    try {
      // Por enquanto, vamos buscar do backend
      // Em produção, você pode criar uma rota específica para listar vídeos
      // Por enquanto, vamos tentar buscar do índice
      const resposta = await api.get('/api/biblioteca/listar');
      if (resposta.data.success) {
        setVideos(resposta.data.videos || []);
      }
    } catch (err: any) {
      // Se a rota não existir, vamos mostrar uma mensagem
      console.error("Erro ao carregar biblioteca:", err);
      setErro("Biblioteca vazia ou erro ao carregar vídeos");
      setVideos([]);
    } finally {
      setCarregando(false);
    }
  };

  const formatarData = (dataISO: string) => {
    try {
      const data = new Date(dataISO);
      return data.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dataISO;
    }
  };

  const handleAbrirVideo = (videoId: string) => {
    navigate(`/resultados/${videoId}`);
  };

  if (carregando) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 text-white flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="animate-spin w-12 h-12 mx-auto text-blue-500" />
          <p className="text-zinc-400">Carregando biblioteca...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 text-white">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <BookOpen className="text-blue-500" />
            Biblioteca de Vídeos
          </h1>
          <p className="text-zinc-400 mt-2">
            Seus vídeos processados e shorts gerados
          </p>
        </div>

        {/* Erro */}
        {erro && videos.length === 0 && (
          <div className="bg-zinc-800/50 backdrop-blur-sm p-12 rounded-xl border border-zinc-700 text-center">
            <FileVideo className="w-16 h-16 mx-auto text-zinc-500 mb-4" />
            <h2 className="text-2xl font-bold mb-2">Biblioteca vazia</h2>
            <p className="text-zinc-400 mb-6">
              Processe vídeos para vê-los aparecer aqui
            </p>
            <button
              onClick={() => navigate("/")}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition"
            >
              Processar Novo Vídeo
            </button>
          </div>
        )}

        {/* Lista de Vídeos */}
        {videos.length > 0 ? (
          <div className="grid gap-4">
            {videos.map((video) => (
              <div
                key={video.video_id}
                className="bg-zinc-800/50 backdrop-blur-sm p-6 rounded-xl border border-zinc-700 hover:border-zinc-600 transition cursor-pointer"
                onClick={() => handleAbrirVideo(video.video_id)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <h3 className="text-xl font-bold text-white line-clamp-2">
                      {video.titulo}
                    </h3>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-400">
                      <div className="flex items-center gap-1">
                        <Calendar size={16} />
                        {formatarData(video.ultima_atualizacao)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Eye size={16} />
                        Ver detalhes
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAbrirVideo(video.video_id);
                    }}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition whitespace-nowrap"
                  >
                    <Play size={18} />
                    Abrir
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : !erro ? (
          <div className="bg-zinc-800/50 backdrop-blur-sm p-12 rounded-xl border border-zinc-700 text-center">
            <FileVideo className="w-16 h-16 mx-auto text-zinc-500 mb-4" />
            <h2 className="text-2xl font-bold mb-2">Nenhum vídeo encontrado</h2>
            <p className="text-zinc-400 mb-6">
              Comece processando um vídeo do YouTube
            </p>
            <button
              onClick={() => navigate("/")}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition"
            >
              Processar Novo Vídeo
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default PaginaBiblioteca;
