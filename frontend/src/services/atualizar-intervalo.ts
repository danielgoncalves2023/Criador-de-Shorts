import { api } from "./api";
import type { SugestaoShort } from "./analisar-video";

export interface AtualizarIntervaloPayload {
  video_id: string;
  indice: number;
  inicio_segundos: number;
  fim_segundos: number;
}

export interface AtualizarIntervaloResposta {
  success: boolean;
  sugestao?: SugestaoShort;
  indice?: number;
  error?: string;
}

const atualizarIntervalo = async (
  payload: AtualizarIntervaloPayload
): Promise<AtualizarIntervaloResposta> => {
  const { data } = await api.post<AtualizarIntervaloResposta>(
    "/api/analise/atualizar-intervalo",
    payload
  );
  return data;
};

export default atualizarIntervalo;

