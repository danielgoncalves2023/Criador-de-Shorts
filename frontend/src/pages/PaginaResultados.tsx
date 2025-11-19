/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Loader2,
  Download,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowLeft,
  AlertCircle,
  FileVideo,
  RefreshCcw,
  Save
} from "lucide-react";
import baixarAudio from "../services/baixar-audio";
import transcreverAudio from "../services/transcrever-audio";
import analisarVideo from "../services/analisar-video";
import baixarShort from "../services/baixar-short";
import obterEstadoVideo, { type EstadoProcessamento } from "../services/obter-estado";
import obterDadosVideo from "../services/obter-dados-video";
import type { SugestaoShort } from "../services/analisar-video";
import atualizarIntervalo from "../services/atualizar-intervalo";

const formatarTempo = (segundos: number) => {
  const m = Math.floor(segundos / 60);
  const s = Math.floor(segundos % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const DURACAO_MINIMA = 40;
const DURACAO_MAXIMA = 180;

const PaginaResultados = () => {
  const { videoId } = useParams<{ videoId: string }>();
  const navigate = useNavigate();
  
  const [estado, setEstado] = useState<EstadoProcessamento | null>(null);
  const [sugestoes, setSugestoes] = useState<SugestaoShort[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [processando, setProcessando] = useState(false);
  const [etapaAtual, setEtapaAtual] = useState<string>("");
  const [erro, setErro] = useState("");
  const [shortsBaixando, setShortsBaixando] = useState<Set<number>>(new Set());
  const [urlVideo, setUrlVideo] = useState<string | null>(null);
  const [reanalisando, setReanalisando] = useState(false);
  const [intervalosEditados, setIntervalosEditados] = useState<Record<number, { inicio: number; fim: number }>>({});
  const [salvandoIntervalo, setSalvandoIntervalo] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (videoId) {
      carregarDados();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId]);

  const carregarDados = async () => {
    if (!videoId) return;
    
    setCarregando(true);
    setErro("");
    
    try {
      // Carrega dados completos do vídeo (incluindo URL)
      const dadosResposta = await obterDadosVideo(videoId);
      if (dadosResposta.success) {
        setUrlVideo(dadosResposta.url || null);
        
        // Se já tem análise, carrega sugestões
        if (dadosResposta.analise?.sugestoes) {
          setSugestoes(dadosResposta.analise.sugestoes);
        }
      }
      
      // Carrega estado do processamento
      const estadoResposta = await obterEstadoVideo(videoId);
      if (estadoResposta.success && estadoResposta.estado) {
        setEstado(estadoResposta.estado);
        
        // Se já tem análise mas não carregou sugestões acima, tenta carregar
        if (estadoResposta.estado.analise && sugestoes.length === 0) {
          await carregarSugestoes();
        }
      }
    } catch (err: any) {
      setErro(err.message || "Erro ao carregar dados");
    } finally {
      setCarregando(false);
    }
  };

  const carregarSugestoes = async () => {
    if (!videoId) return;
    
    try {
      // Busca informações do vídeo para obter URL
      // Por enquanto, vamos tentar buscar do estado salvo
      // Em produção, você pode salvar a URL no estado ou buscar de outra forma
      const resposta = await analisarVideo({ video_id: videoId });
      if (resposta.success && resposta.sugestoes) {
        setSugestoes(resposta.sugestoes);
      }
    } catch (err) {
      console.error("Erro ao carregar sugestões:", err);
    }
  };

  const handleReanalise = async () => {
    if (!videoId) return;
    if (!window.confirm("Refazer a análise substituirá todas as sugestões atuais. Deseja continuar?")) {
      return;
    }
    setReanalisando(true);
    setErro("");
    try {
      const resposta = await analisarVideo({ video_id: videoId, reprocessar: true });
      if (resposta.success && resposta.sugestoes) {
        setSugestoes(resposta.sugestoes);
        setIntervalosEditados({});
        setEstado(prev => prev ? { ...prev, analise: true } : prev);
      } else {
        setErro(resposta.error || "Erro ao reanalisar o vídeo");
      }
    } catch (err: any) {
      setErro(err.message || "Erro ao reanalisar o vídeo");
    } finally {
      setReanalisando(false);
    }
  };

  const processarVideoCompleto = async () => {
    if (!videoId) return;
    
    setProcessando(true);
    setErro("");
    
    try {
      // Busca URL do vídeo se não tiver
      let urlParaUsar = urlVideo;
      if (!urlParaUsar) {
        setEtapaAtual("Buscando informações do vídeo...");
        const dadosResposta = await obterDadosVideo(videoId);
        if (dadosResposta.success && dadosResposta.url) {
          urlParaUsar = dadosResposta.url;
          setUrlVideo(urlParaUsar);
        } else {
          setErro("URL do vídeo não encontrada. Volte à página inicial e processe novamente.");
          setProcessando(false);
          return;
        }
      }
      
      if (!urlParaUsar) {
        setErro("URL do vídeo não disponível");
        setProcessando(false);
        return;
      }
      
      // Etapa 1: Baixar áudio (se necessário)
      if (!estado?.audio) {
        setEtapaAtual("Baixando áudio do vídeo...");
        const respostaAudio = await baixarAudio(urlParaUsar, videoId);
        if (!respostaAudio.success) {
          setErro(respostaAudio.error || "Erro ao baixar áudio");
          setProcessando(false);
          return;
        }
        // Atualiza estado
        setEstado(prev => prev ? { ...prev, audio: true } : null);
      }
      
      // Etapa 2: Transcrever (se necessário)
      if (!estado?.transcricao) {
        setEtapaAtual("Transcrevendo áudio com Whisper...");
        // Busca dados atualizados para obter caminho do áudio
        const dadosAtualizados = await obterDadosVideo(videoId);
        if (dadosAtualizados.success && dadosAtualizados.audio?.caminho_arquivo) {
          const respostaTranscricao = await transcreverAudio({
            audio_path: dadosAtualizados.audio.caminho_arquivo,
            video_id: videoId,
            url: urlParaUsar
          });
          
          if (!respostaTranscricao.success) {
            setErro(respostaTranscricao.error || "Erro ao transcrever áudio");
            setProcessando(false);
            return;
          }
          // Atualiza estado
          setEstado(prev => prev ? { ...prev, transcricao: true } : null);
        } else {
          setErro("Caminho do áudio não encontrado");
          setProcessando(false);
          return;
        }
      }
      
      // Etapa 3: Analisar (se necessário)
      if (!estado?.analise) {
        setEtapaAtual("Analisando vídeo com IA Ollama...");
        // Busca transcrição para enviar à análise
        const dadosAtualizados = await obterDadosVideo(videoId);
        const transcricaoTexto = dadosAtualizados.transcricao?.texto;
        
        if (!transcricaoTexto) {
          setErro("Transcrição não encontrada. Transcreva o áudio primeiro.");
          setProcessando(false);
          return;
        }
        
        const resposta = await analisarVideo({ 
          video_id: videoId,
          transcricao_texto: transcricaoTexto
        });
        
        if (resposta.success && resposta.sugestoes) {
          setSugestoes(resposta.sugestoes);
          setEstado(prev => prev ? { ...prev, analise: true } : null);
        } else {
          setErro(resposta.error || "Erro ao analisar vídeo");
        }
      }
      
    } catch (err: any) {
      setErro(err.message || "Erro ao processar vídeo");
    } finally {
      setProcessando(false);
      setEtapaAtual("");
    }
  };

  const handleBaixarShort = async (sugestao: SugestaoShort, indice: number) => {
    if (!videoId) return;
    
    setShortsBaixando(prev => new Set(prev).add(indice));
    setErro("");
    
    try {
      const resposta = await baixarShort({
        video_id: videoId,
        inicio_segundos: sugestao.inicio_segundos,
        fim_segundos: sugestao.fim_segundos,
        titulo: sugestao.titulo,
        indice_sugestao: indice
      });
      
      if (resposta.success) {
        // Atualiza estado
        setEstado(prev => prev ? { ...prev, shorts: true } : null);
      } else {
        setErro(resposta.error || "Erro ao baixar short");
      }
    } catch (err: any) {
      setErro(err.message || "Erro ao baixar short");
    } finally {
      setShortsBaixando(prev => {
        const novo = new Set(prev);
        novo.delete(indice);
        return novo;
      });
    }
  };

  const obterIntervaloAtual = (indice: number) => {
    const editado = intervalosEditados[indice];
    return {
      inicio: editado?.inicio ?? sugestoes[indice]?.inicio_segundos ?? 0,
      fim: editado?.fim ?? sugestoes[indice]?.fim_segundos ?? 0
    };
  };

  const ajustarIntervaloLocal = (indice: number, campo: "inicio" | "fim", valor: number) => {
    setIntervalosEditados(prev => {
      const atual = prev[indice] ?? {
        inicio: sugestoes[indice]?.inicio_segundos ?? 0,
        fim: sugestoes[indice]?.fim_segundos ?? 0
      };
      return {
        ...prev,
        [indice]: {
          ...atual,
          [campo]: isNaN(valor) ? atual[campo] : valor
        }
      };
    });
  };

  const handleSalvarIntervalo = async (indice: number) => {
    if (!videoId) return;
    const sugestaoAtual = sugestoes[indice];
    if (!sugestaoAtual) return;

    const { inicio, fim } = obterIntervaloAtual(indice);

    if (fim <= inicio) {
      setErro("O tempo final precisa ser maior que o inicial.");
      return;
    }

    const duracao = fim - inicio;
    if (duracao < DURACAO_MINIMA || duracao > DURACAO_MAXIMA) {
      setErro("Os shorts devem ter entre 40 segundos e 3 minutos.");
      return;
    }

    setErro("");
    setSalvandoIntervalo(prev => new Set(prev).add(indice));

    try {
      const resposta = await atualizarIntervalo({
        video_id: videoId,
        indice,
        inicio_segundos: inicio,
        fim_segundos: fim
      });

      if (resposta.success && resposta.sugestao) {
        const sugestaoAtualizada = resposta.sugestao;
        setSugestoes(prev =>
          prev.map((item, idx) => (idx === indice ? sugestaoAtualizada : item))
        );
        setIntervalosEditados(prev => {
          const novo = { ...prev };
          delete novo[indice];
          return novo;
        });
      } else {
        setErro(resposta.error || "Não foi possível salvar o intervalo.");
      }
    } catch (err: any) {
      setErro(err.message || "Erro ao salvar o intervalo.");
    } finally {
      setSalvandoIntervalo(prev => {
        const novo = new Set(prev);
        novo.delete(indice);
        return novo;
      });
    }
  };

  if (carregando) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 text-white flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="animate-spin w-12 h-12 mx-auto text-blue-500" />
          <p className="text-zinc-400">Carregando resultados...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 text-white">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition mb-4"
          >
            <ArrowLeft size={20} />
            Voltar
          </button>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Sparkles className="text-yellow-500" />
            Sugestões de Shorts
          </h1>
        </div>

        <div className="flex flex-wrap gap-3 mb-6">
          {!estado?.analise && (
            <button
              onClick={processarVideoCompleto}
              disabled={processando}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded-lg transition disabled:opacity-50"
            >
              <Loader2 className={processando ? "animate-spin" : ""} size={18} />
              Processar vídeo completo
            </button>
          )}
          {estado?.analise && (
            <button
              onClick={handleReanalise}
              disabled={reanalisando}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold px-4 py-2 rounded-lg transition disabled:opacity-50"
            >
              {reanalisando ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                <RefreshCcw size={18} />
              )}
              Reanalizar vídeo
            </button>
          )}
        </div>

        {/* Estado do Processamento */}
        {estado && (
          <div className="bg-zinc-800/50 backdrop-blur-sm p-6 rounded-xl border border-zinc-700 mb-6">
            <h2 className="text-lg font-semibold mb-4">Status do Processamento</h2>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
              {[
                { key: 'info_video', label: 'Info', icon: CheckCircle2 },
                { key: 'audio', label: 'Áudio', icon: FileVideo },
                { key: 'transcricao', label: 'Transcrição', icon: CheckCircle2 },
                { key: 'analise', label: 'Análise IA', icon: Sparkles },
                { key: 'shorts', label: 'Shorts', icon: Download },
              ].map(({ key, label, icon: Icon }) => (
                <div
                  key={key}
                  className={`flex flex-col items-center gap-2 p-3 rounded-lg ${
                    estado[key as keyof EstadoProcessamento]
                      ? 'bg-green-900/20 border border-green-500/50'
                      : 'bg-zinc-900/50 border border-zinc-700'
                  }`}
                >
                  <Icon
                    size={24}
                    className={
                      estado[key as keyof EstadoProcessamento]
                        ? 'text-green-500'
                        : 'text-zinc-500'
                    }
                  />
                  <span className="text-xs text-zinc-400">{label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Erro */}
        {erro && (
          <div className="bg-red-900/20 border border-red-500/50 rounded-xl p-4 mb-6 flex items-center gap-3">
            <AlertCircle className="text-red-500" size={20} />
            <span className="text-red-400">{erro}</span>
          </div>
        )}

        {/* Processamento */}
        {processando && (
          <div className="bg-blue-900/20 border border-blue-500/50 rounded-xl p-6 mb-6">
            <div className="flex items-center gap-3">
              <Loader2 className="animate-spin text-blue-500" size={24} />
              <div>
                <p className="font-semibold">{etapaAtual}</p>
                <p className="text-sm text-zinc-400">Aguarde, isso pode levar alguns minutos...</p>
              </div>
            </div>
          </div>
        )}

        {/* Sugestões */}
        {sugestoes.length > 0 ? (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold">
              {sugestoes.length} Sugestões de Shorts Encontradas
            </h2>
            <p className="text-sm text-zinc-400 mb-2">
              Cada short precisa ter entre 40 segundos e 3 minutos. Ajuste os tempos, visualize o trecho no player e salve o intervalo antes de baixar.
            </p>
            <div className="grid gap-4">
              {sugestoes.map((sugestao, indice) => {
                const intervaloAtual = obterIntervaloAtual(indice);
                return (
                <div
                  key={indice}
                  className="bg-zinc-800/50 backdrop-blur-sm p-6 rounded-xl border border-zinc-700 hover:border-zinc-600 transition"
                >
                  <div className="flex flex-col lg:flex-row gap-6">
                    <div className="flex-1 space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <h3 className="text-xl font-bold text-white">
                          {sugestao.titulo}
                        </h3>
                        <div className="flex items-center gap-2 text-sm text-zinc-400 whitespace-nowrap">
                          <Clock size={16} />
                          {formatarTempo(sugestao.inicio_segundos)} - {formatarTempo(sugestao.fim_segundos)}
                        </div>
                      </div>
                      
                      <p className="text-zinc-300">{sugestao.descricao}</p>
                      
                      {sugestao.hook && (
                        <div className="bg-zinc-900/50 p-3 rounded-lg border border-zinc-700">
                          <p className="text-sm text-zinc-400 mb-1">Hook sugerido:</p>
                          <p className="text-white font-medium">"{sugestao.hook}"</p>
                        </div>
                      )}
                      
                      {sugestao.potencial_viral && (
                        <div className="bg-yellow-900/20 p-3 rounded-lg border border-yellow-500/50">
                          <p className="text-sm text-yellow-400 font-semibold mb-1">
                            Potencial Viral:
                          </p>
                          <p className="text-yellow-200 text-sm">{sugestao.potencial_viral}</p>
                        </div>
                      )}
                      
                      {sugestao.tags && sugestao.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {sugestao.tags.map((tag, tagIdx) => (
                            <span
                              key={tagIdx}
                              className="px-2 py-1 bg-blue-900/30 text-blue-300 text-xs rounded"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="w-full lg:w-80 flex flex-col gap-4">
                      {videoId && (
                        <div className="w-full aspect-video bg-black/60 rounded-lg overflow-hidden border border-zinc-700">
                          <iframe
                            key={`${indice}-${Math.round(intervaloAtual.inicio * 10)}-${Math.round(intervaloAtual.fim * 10)}`}
                            src={`https://www.youtube.com/embed/${videoId}?modestbranding=1&rel=0&start=${Math.floor(intervaloAtual.inicio)}&end=${Math.floor(intervaloAtual.fim)}&controls=1`}
                            title={`preview-${indice}`}
                            className="w-full h-full"
                            loading="lazy"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                            referrerPolicy="no-referrer-when-downgrade"
                          />
                        </div>
                      )}

                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <label className="flex flex-col gap-1 text-zinc-300">
                          Início (s)
                          <input
                            type="number"
                            min={0}
                            step={0.1}
                            value={intervaloAtual.inicio}
                            onChange={(e) => ajustarIntervaloLocal(indice, "inicio", parseFloat(e.target.value))}
                            className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white"
                          />
                        </label>
                        <label className="flex flex-col gap-1 text-zinc-300">
                          Fim (s)
                          <input
                            type="number"
                            min={0}
                            step={0.1}
                            value={intervaloAtual.fim}
                            onChange={(e) => ajustarIntervaloLocal(indice, "fim", parseFloat(e.target.value))}
                            className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white"
                          />
                        </label>
                      </div>
                      <div className="text-xs text-zinc-400">
                        Duração atual: {formatarTempo(intervaloAtual.fim - intervaloAtual.inicio)}
                      </div>

                      <button
                        onClick={() => handleSalvarIntervalo(indice)}
                        disabled={salvandoIntervalo.has(indice)}
                        className="flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-700 text-white font-semibold px-4 py-3 rounded-lg transition disabled:opacity-50"
                      >
                        {salvandoIntervalo.has(indice) ? (
                          <Loader2 className="animate-spin" size={18} />
                        ) : (
                          <>
                            <Save size={18} />
                            Salvar intervalo
                          </>
                        )}
                      </button>

                      <button
                        onClick={() => handleBaixarShort(sugestao, indice)}
                        disabled={shortsBaixando.has(indice)}
                        className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {shortsBaixando.has(indice) ? (
                          <>
                            <Loader2 className="animate-spin" size={18} />
                            Baixando...
                          </>
                        ) : (
                          <>
                            <Download size={18} />
                            Baixar Short
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              );})}
            </div>
          </div>
        ) : (
          <div className="bg-zinc-800/50 backdrop-blur-sm p-12 rounded-xl border border-zinc-700 text-center">
            <Sparkles className="w-16 h-16 mx-auto text-zinc-500 mb-4" />
            <h2 className="text-2xl font-bold mb-2">Nenhuma sugestão encontrada</h2>
            <p className="text-zinc-400 mb-6">
              Processe o vídeo para gerar sugestões de shorts virais
            </p>
            {!estado?.analise && (
              <button
                onClick={processarVideoCompleto}
                disabled={processando}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition disabled:opacity-50"
              >
                {processando ? "Processando..." : "Processar Vídeo"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PaginaResultados;
