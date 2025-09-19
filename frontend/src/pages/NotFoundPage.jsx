import { Link } from 'react-router-dom';
import './NotFoundPage.css';

// Você pode escolher uma animação de sua preferência. Esta é uma ótima sugestão:
const gifUrl = "https://cdn.dribbble.com/users/285475/screenshots/2083086/dribbble_1.gif";

function NotFoundPage() {
  return (
    <div className="not-found-container">
      <div className="not-found-content">
        <img src={gifUrl} alt="Animação de pessoa perdida" className="not-found-gif" />
        <h1>Salmos 119:29</h1>
        <p>
          "Vê se há em mim algum caminho mau, e guia-me pelo caminho eterno". 
        </p>
        <p>
          Esse caminho que você veio, não existe 👀
        </p>
        <Link to="/dashboard" className="back-home-btn">
          Voltar para o Painel
        </Link>
      </div>
    </div>
  );
}

export default NotFoundPage;