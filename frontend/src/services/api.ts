import axios from 'axios';

// URL base do seu backend FastAPI
const BACKEND_URL = "http://localhost:5000";

/**
 * Instância customizada do Axios para comunicação com o backend.
 */
export const api = axios.create({
    baseURL: BACKEND_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});