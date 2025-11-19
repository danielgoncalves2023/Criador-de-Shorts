/* eslint-disable @typescript-eslint/no-explicit-any */
import { api } from "./api";

interface BaixarShortParams {
  video_id?: string;
  url?: string;
  inicio_segundos: number;
  fim_segundos: number;
  titulo?: string;
  indice_sugestao?: number;
}

interface RespostaBaixarShort {
  success: boolean;
  caminho_arquivo?: string;
  video_id?: string;
  cache?: boolean;
  error?: string;
}

const baixarShort = async (params: BaixarShortParams): Promise<RespostaBaixarShort> => {
  try {
    const { data } = await api.post<RespostaBaixarShort>('/api/shorts/baixar', params);
    return data;
  } catch (erro: any) {
    console.error('Falha ao baixar short:', erro);
    throw new Error(erro.response?.data?.error || 'Erro ao baixar short');
  }
};

export default baixarShort;

