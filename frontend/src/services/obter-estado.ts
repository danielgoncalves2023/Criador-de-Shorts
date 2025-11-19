import { api } from "./api";

interface EstadoProcessamento {
  info_video: boolean;
  audio: boolean;
  transcricao: boolean;
  analise: boolean;
  shorts: boolean;
}

interface RespostaEstado {
  success: boolean;
  estado?: EstadoProcessamento;
  error?: string;
}

const obterEstadoVideo = async (videoId: string): Promise<RespostaEstado> => {
  try {
    const { data } = await api.get<RespostaEstado>(`/api/youtube/estado/${videoId}`);
    return data;
  } catch (erro: any) {
    console.error('Falha ao obter estado:', erro);
    throw new Error(erro.response?.data?.error || 'Erro ao obter estado do vídeo');
  }
};

export default obterEstadoVideo;
export type { EstadoProcessamento };

