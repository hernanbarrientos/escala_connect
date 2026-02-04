import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import Spinner from '../components/Spinner';
import './DashboardPage.css'; // Reaproveita o estilo do Dashboard

function MinisterioPage() {
  const { id } = useParams(); // Pega o ID da URL (ex: /ministerio/5)
  const navigate = useNavigate();
  const [ministerio, setMinisterio] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMinisterioData() {
      try {
        // 1. Busca os detalhes desse ministério específico
        // (Você precisará criar essa rota no backend se quiser detalhes finos,
        // mas por enquanto vamos filtrar da lista geral ou criar um endpoint simples)
        const resStats = await api.get(`/ministerios/${id}/dashboard`);
        setStats(resStats.data);
        
        // Simulação de pegar o nome (ideal seria um endpoint /ministerios/{id})
        // Por enquanto vamos focar nos dados do dashboard
        setMinisterio({ nome: "Ministério " + id }); 
      } catch (error) {
        console.error("Erro ao carregar ministério", error);
      } finally {
        setLoading(false);
      }
    }
    fetchMinisterioData();
  }, [id]);

  if (loading) return <Spinner text="Entrando no ministério..." />;

  return (
    <div className="dashboard-container">
      {/* CABEÇALHO DO MINISTÉRIO */}
      <header className="hub-header" style={{ borderBottom: `4px solid ${ministerio?.cor || '#3b82f6'}` }}>
        <div>
          <button onClick={() => navigate('/dashboard')} className="back-link">← Voltar para o HUB</button>
          <h1>Painel do Ministério</h1>
        </div>
        <div className="ministerio-badge">ID: {id}</div>
      </header>

      {/* MENU DE AÇÕES RÁPIDAS */}
      <div className="actions-grid">
        <button className="action-card" onClick={() => navigate(`/ministerio/${id}/voluntarios`)}>
          <span className="icon">👥</span>
          <h3>Voluntários</h3>
          <p>Gerenciar equipe</p>
        </button>

        <button className="action-card" onClick={() => navigate(`/ministerio/${id}/escalas`)}>
          <span className="icon">📅</span>
          <h3>Escalas</h3>
          <p>Montar e visualizar</p>
        </button>

        <button className="action-card" onClick={() => navigate(`/ministerio/${id}/funcoes`)}>
          <span className="icon">🔧</span>
          <h3>Funções</h3>
          <p>Configurar cargos</p>
        </button>
      </div>

      {/* ESTATÍSTICAS DO MINISTÉRIO */}
      <div className="kpi-grid" style={{ marginTop: '2rem' }}>
        <div className="kpi-card">
          <h3>Voluntários Ativos</h3>
          <p className="kpi-value">{stats?.kpis?.voluntarios_ativos || 0}</p>
        </div>
        <div className="kpi-card">
          <h3>Escalas no Mês</h3>
          <p className="kpi-value">{stats?.kpis?.eventos_mes || 0}</p>
        </div>
      </div>
    </div>
  );
}

export default MinisterioPage;