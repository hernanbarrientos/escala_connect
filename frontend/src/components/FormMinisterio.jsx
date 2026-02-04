import { useState } from 'react';
import api from '../services/api';
import './FormVoluntario.css'; // Podemos reaproveitar o CSS dos outros forms

function FormMinisterio({ onSave, onCancel }) {
  const [nome, setNome] = useState('');
  const [cor, setCor] = useState('#3b82f6'); // Azul padrão
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.post('/igreja/ministerios', {
        nome,
        cor_hex: cor
      });
      onSave(); // Avisa o Dashboard que salvou
    } catch (err) {
      console.error(err);
      setError('Erro ao criar ministério.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form-container">
      {error && <p className="error-message">{error}</p>}

      <div className="form-group">
        <label>Nome do Ministério</label>
        <input
          type="text"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          placeholder="Ex: Louvor, Kids, Recepção..."
          required
        />
      </div>

      <div className="form-group">
        <label>Cor de Identificação</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <input
            type="color"
            value={cor}
            onChange={(e) => setCor(e.target.value)}
            style={{ width: '50px', height: '50px', padding: 0, border: 'none' }}
          />
          <span style={{ color: '#888' }}>Escolha uma cor para os cards</span>
        </div>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-cancel" disabled={loading}>
          Cancelar
        </button>
        <button type="submit" className="btn-save" disabled={loading}>
          {loading ? 'Criando...' : 'Criar Ministério'}
        </button>
      </div>
    </form>
  );
}

export default FormMinisterio;