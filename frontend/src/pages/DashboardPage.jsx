import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';
import Spinner from '../components/Spinner';
import Modal from '../components/Modal'; // Importando Modal
import FormMinisterio from '../components/FormMinisterio'; // Importando o Form
import './DashboardPage.css';

function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [ministerios, setMinisterios] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Estado para controlar o Modal
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchData = async () => {
    try {
      const [resStats, resMinisterios] = await Promise.all([
        api.get('/igreja/dashboard'),
        api.get('/igreja/ministerios')
      ]);
      setStats(resStats.data);
      setMinisterios(resMinisterios.data);
    } catch (error) {
      console.error("Erro ao carregar dashboard", error);
      if (error.response?.status === 401) logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleMinisterioCreated = () => {
    setIsModalOpen(false);
    fetchData(); // Recarrega a lista para aparecer o novo ministério
  };

  if (loading) return <Spinner text="Carregando o Hub..." />;

  return (
    <div className="dashboard-container">
      <header className="hub-header">
        <div>
          <h1>Olá, {user?.name}</h1>
          <p className="church-name">{user?.church}</p>
        </div>
        <button onClick={logout} className="logout-btn">Sair</button>
      </header>

      <div className="kpi-grid">
        <div className="kpi-card">
          <h3>Total de Voluntários</h3>
          <p className="kpi-value">{stats?.total_voluntarios || 0}</p>
        </div>
        <div className="kpi-card">
          <h3>Eventos no Mês</h3>
          <p className="kpi-value">{stats?.total_eventos || 0}</p>
        </div>
        <div className="kpi-card">
          <h3>Ministérios Ativos</h3>
          <p className="kpi-value">{ministerios.length}</p>
        </div>
      </div>

      <section className="ministerios-section">
        <div className="section-header">
          <h2>Seus Ministérios</h2>
          {/* Botão agora abre o Modal */}
          <button className="add-btn" onClick={() => setIsModalOpen(true)}>+ Novo</button>
        </div>

        {ministerios.length === 0 ? (
          <div className="empty-state">
            <p>Nenhum ministério cadastrado ainda.</p>
            <button className="btn-primary" onClick={() => setIsModalOpen(true)}>
              Criar o Primeiro
            </button>
          </div>
        ) : (
          <div className="ministerios-grid">
            {ministerios.map((min) => (
              <div 
                key={min.id_ministerio} 
                className="ministerio-card"
                style={{ borderLeft: `5px solid ${min.cor_hex}` }}
                onClick={() => navigate(`/ministerio/${min.id_ministerio}`)}
              >
                <h3>{min.nome}</h3>
                <span className="arrow-icon">→</span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* MODAL DE CRIAÇÃO */}
      <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)}
        title="Novo Ministério"
      >
        <FormMinisterio 
          onSave={handleMinisterioCreated} 
          onCancel={() => setIsModalOpen(false)} 
        />
      </Modal>
    </div>
  );
}

export default DashboardPage;