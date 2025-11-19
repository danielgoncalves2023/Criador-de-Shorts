import { api } from "./api";

interface AnalisarVideoParams {
  video_id?: string;
  url?: string;
  transcricao_texto?: string;
  reprocessar?: boolean;
}

interface SugestaoShort {
  titulo: string;
  inicio_segundos: number;
  fim_segundos: number;
  duracao_segundos: number;
  descricao: string;
  potencial_viral: string;
  hook: string;
  tags: string[];
}

interface RespostaAnalise {
  success: boolean;
  sugestoes?: SugestaoShort[];
  video_id?: string;
  cache?: boolean;
  error?: string;
}

const analisarVideo = async (params: AnalisarVideoParams): Promise<RespostaAnalise> => {
  try {
    const { data } = await api.post<RespostaAnalise>('/api/analise/gerar-sugestoes', params);
    return data;
  } catch (erro: any) {
    console.error('Falha na análise:', erro);
    throw new Error(erro.response?.data?.error || 'Erro ao analisar vídeo');
  }
};

export default analisarVideo;
export type { SugestaoShort };

