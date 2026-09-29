import React from 'react';
import { motion } from 'framer-motion';

interface Props {
  message?: string;
  onRetry?: () => void;
}

const ErrorState: React.FC<Props> = ({
  message = 'Something went wrong while fetching recommendations.',
  onRetry,
}) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      textAlign: 'center',
      padding: 'var(--sp-xl)',
      maxWidth: 480,
      margin: '0 auto',
    }}
  >
    <div
      style={{
        width: 80,
        height: 80,
        borderRadius: '50%',
        background: 'rgba(147, 0, 10, 0.15)',
        border: '1px solid rgba(255,180,171,0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 'var(--sp-lg)',
      }}
    >
      <span className="material-symbols-outlined" style={{ fontSize: 40, color: 'var(--error)' }}>
        error_outline
      </span>
    </div>
    <h2 className="headline-lg" style={{ color: 'var(--on-surface)', marginBottom: 'var(--sp-xs)' }}>
      Oops! Something went wrong
    </h2>
    <p className="body-sm" style={{ color: 'var(--on-surface-variant)', marginBottom: 'var(--sp-lg)' }}>
      {message}
    </p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="brand-gradient-bg"
        style={{
          border: 'none',
          borderRadius: 'var(--radius-full)',
          padding: '10px 28px',
          color: 'white',
          fontWeight: 600,
          fontSize: 14,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontFamily: "'Inter', sans-serif",
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>refresh</span>
        Try Again
      </button>
    )}
  </motion.div>
);

export default ErrorState;
