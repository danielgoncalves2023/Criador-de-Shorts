/* eslint-disable @typescript-eslint/no-explicit-any */
import { api } from "./api";

interface RespostaBaixarAudio {
  success: boolean;
  audio_path?: string;
  video_id?: string;
  cache?: boolean;
  error?: string;
}

const baixarAudio = async (urlDoVideo: string, videoId?: string): Promise<RespostaBaixarAudio> => {
  try {
    const { data } = await api.post<RespostaBaixarAudio>('/api/audio/download', { 
      url: urlDoVideo,
      video_id: videoId
    });
    return data;
  } catch (erro: any) {
    console.error('Falha na requisição:', erro);
    throw new Error(erro.response?.data?.error || 'Erro ao baixar áudio');
  }
};

export default baixarAudio;