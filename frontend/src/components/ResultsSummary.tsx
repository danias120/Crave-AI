import React from 'react';
import { motion } from 'framer-motion';

interface Props {
  summary: string;
}

const ResultsSummary: React.FC<Props> = ({ summary }) => (
  <motion.div
    className="glass-panel"
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
    style={{
      borderRadius: 'var(--radius-md)',
      borderLeft: '3px solid var(--primary-container)',
      padding: 'var(--sp-md) var(--sp-lg)',
      display: 'flex',
      alignItems: 'flex-start',
      gap: 'var(--sp-sm)',
    }}
  >
    <span
      className="material-symbols-outlined filled"
      style={{ color: 'var(--tertiary)', fontSize: 22, marginTop: 2 }}
    >
      auto_awesome
    </span>
    <p className="body-sm" style={{ color: 'var(--on-surface-variant)', lineHeight: 1.6, margin: 0 }}>
      {summary}
    </p>
  </motion.div>
);

export default ResultsSummary;
