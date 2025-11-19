import { api } from "./api";

interface InfoVideo {
  titulo: string;
  autor: string;
  duracao_segundos: number;
  data_publicacao: string;
  descricao: string;
  url_thumbnail: string;
  visualizacoes: number;
  video_id: string;
}

interface RespostaInfoVideo {
  success: boolean;
  video_info?: InfoVideo;
  video_id?: string;
  cache?: boolean;
  error?: string;
}

const buscarInfoYoutube = async (urlDoVideo: string): Promise<RespostaInfoVideo> => {
  try {
    const { data } = await api.post<RespostaInfoVideo>('/api/youtube/info', { url: urlDoVideo });
    return data;
  } catch (erro: any) {
    console.error('Falha na requisição:', erro);
    throw new Error(erro.response?.data?.error || 'Erro ao buscar informações do vídeo');
  }
};

export default buscarInfoYoutube;
export type { InfoVideo };