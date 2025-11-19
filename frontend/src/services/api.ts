import axios from 'axios';

const BACKEND_URL = "http://localhost:5000";

export const api = axios.create({
    baseURL: BACKEND_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor para debug
api.interceptors.request.use(
    (config) => {
        console.log('[API] Requisição:', config.method?.toUpperCase(), config.url);
        return config;
    },
    (error) => {
        console.error('[API] Erro na requisição:', error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        console.log('[API] Resposta:', response.status, response.data);
        return response;
    },
    (error) => {
        console.error('[API] Erro na resposta:', error.response?.status, error.message);
        return Promise.reject(error);
    }
);