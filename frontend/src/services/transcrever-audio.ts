import { api } from "./api";

interface TranscreverAudioParams {
  audio_path: string;
  video_id?: string;
  url?: string;
}

interface SegmentoTranscricao {
  inicio: number;
  fim: number;
  texto: string;
}

interface RespostaTranscricao {
  success: boolean;
  transcricao?: SegmentoTranscricao[];
  texto_completo?: string;
  video_id?: string;
  cache?: boolean;
  error?: string;
}

const transcreverAudio = async (params: TranscreverAudioParams): Promise<RespostaTranscricao> => {
  try {
    const { data } = await api.post<RespostaTranscricao>('/api/transcricao', params);
    return data;
  } catch (erro: any) {
    console.error('Falha na transcrição:', erro);
    throw new Error(erro.response?.data?.error || 'Erro ao transcrever áudio');
  }
};

export default transcreverAudio;
