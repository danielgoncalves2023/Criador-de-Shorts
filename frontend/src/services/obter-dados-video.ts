import { api } from "./api";

interface DadosVideo {
  video_id: string;
  url: string;
  info_video?: any;
  audio?: any;
  transcricao?: any;
  analise?: any;
  ultima_atualizacao?: string;
}

interface RespostaDadosVideo {
  success: boolean;
  video_id?: string;
  url?: string;
  info_video?: any;
  audio?: any;
  transcricao?: any;
  analise?: any;
  ultima_atualizacao?: string;
  error?: string;
}

const obterDadosVideo = async (videoId: string): Promise<RespostaDadosVideo> => {
  try {
    const { data } = await api.get<RespostaDadosVideo>(`/api/youtube/dados/${videoId}`);
    return data;
  } catch (erro: any) {
    console.error('Falha ao obter dados do vídeo:', erro);
    throw new Error(erro.response?.data?.error || 'Erro ao obter dados do vídeo');
  }
};

export default obterDadosVideo;
export type { DadosVideo };

