import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import PaginaBiblioteca from "./pages/PaginaBiblioteca";
import PaginaInicial from "./pages/PaginaInicial";
import PaginaResultados from "./pages/PaginaResultados";
import Header from "./components/Header";

// Cria um cliente para o React Query
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-950">
          <Header />
          <Routes>
            {/* Rota 1: Home - Inserção de link */}
            <Route path="/" element={<PaginaInicial />} />
            {/* Rota 2: Biblioteca - Lista de vídeos */}
            <Route path="/biblioteca" element={<PaginaBiblioteca />} />
            {/* Rota 3: Resultados - Detalhes dos shorts por ID do vídeo */}
            <Route path="/resultados/:videoId" element={<PaginaResultados />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
