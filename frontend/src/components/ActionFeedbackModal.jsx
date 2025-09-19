// arquivo: frontend/src/components/ActionFeedbackModal.jsx

import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import Spinner from './Spinner';
import './ActionFeedbackModal.css';

// Componente para o estado inicial de confirmação
const ConfirmationView = ({ message, onConfirm, onCancel }) => (
  <div>
    <p className="confirmation-message">{message}</p>
    <div className="form-actions">
      <button onClick={onCancel} className="btn-cancel">Cancelar</button>
      <button onClick={onConfirm} className="btn-confirm">Confirmar</button>
    </div>
  </div>
);

// Componente para o estado de sucesso ou erro
const ResultView = ({ message, onDone, isError }) => (
  <div className="result-view">
    <div className={`result-icon ${isError ? 'error' : 'success'}`}>
      {isError ? '✖' : '✔'}
    </div>
    <p>{message}</p>
    <div className="form-actions">
      <button onClick={onDone} className="btn-confirm">Pronto</button>
    </div>
  </div>
);


function ActionFeedbackModal({ isOpen, onClose, title, confirmationMessage, action, onSuccess }) {
  const [status, setStatus] = useState('confirm'); // 'confirm', 'loading', 'success', 'error'

  // Reseta o estado do modal sempre que ele é reaberto
  useEffect(() => {
    if (isOpen) {
      setStatus('confirm');
    }
  }, [isOpen]);

  const handleConfirm = async () => {
    setStatus('loading');
    try {
      await action();
      setStatus('success');
    } catch (err) {
      console.error("Action failed:", err);
      setStatus('error');
    }
  };

  const handleClose = () => {
    onClose();
    // Se a ação foi um sucesso, chama a função onSuccess para, por exemplo, recarregar os dados da página
    if (status === 'success' && onSuccess) {
      onSuccess();
    }
  };

  const renderContent = () => {
    switch (status) {
      case 'loading':
        return <Spinner text="Processando..." />;
      case 'success':
        return <ResultView message="Ação realizada com sucesso!" onDone={handleClose} isError={false} />;
      case 'error':
        return <ResultView message="Ocorreu um erro. Tente novamente." onDone={handleClose} isError={true} />;
      case 'confirm':
      default:
        return <ConfirmationView message={confirmationMessage} onConfirm={handleConfirm} onCancel={handleClose} />;
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={title}>
      {renderContent()}
    </Modal>
  );
}

export default ActionFeedbackModal;