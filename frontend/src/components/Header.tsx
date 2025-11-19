import { Link, useLocation } from "react-router-dom";
import { Youtube } from "lucide-react";

/**
 * Componente de Cabeçalho (Header) com logo e navegação.
 */
const Header = () => {
  const location = useLocation();
  
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <header className="bg-zinc-900/50 backdrop-blur-sm border-b border-zinc-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition">
          <Youtube className="w-8 h-8 text-red-500" />
          <h1 className="text-2xl font-bold text-white tracking-wider">
            Criador de Shorts
          </h1>
        </Link>
        <nav>
          <ul className="flex space-x-6">
            <li>
              <Link
                to="/"
                className={`transition duration-150 ${
                  isActive("/")
                    ? "text-red-400 font-medium border-b-2 border-red-500 pb-1"
                    : "text-zinc-300 hover:text-white"
                }`}
              >
                Início
              </Link>
            </li>
            <li>
              <Link
                to="/biblioteca"
                className={`transition duration-150 ${
                  isActive("/biblioteca")
                    ? "text-red-400 font-medium border-b-2 border-red-500 pb-1"
                    : "text-zinc-300 hover:text-white"
                }`}
              >
                Biblioteca
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;
