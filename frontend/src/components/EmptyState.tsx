import React from 'react';
import { motion } from 'framer-motion';

interface Props {
  summary?: string | null;
  cuisine?: string | null;
  location?: string | null;
}

const EmptyState: React.FC<Props> = ({ summary, cuisine, location }) => {
  const isAfricanChurchStreet =
    cuisine?.toLowerCase() === 'african' && location?.toLowerCase().includes('church');

  let title = 'No restaurants found 😔';
  let message =
    summary ||
    "Our AI couldn't find restaurants matching your criteria. Try lowering the minimum rating, broadening your budget, or picking a different cuisine.";

  if (isAfricanChurchStreet) {
    title = 'No African Restaurants in Church Street 🌍';
  } else if (cuisine && location) {
    title = `No ${cuisine} restaurants in ${location} 🍽️`;
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        padding: 'var(--sp-xl)',
        maxWidth: 520,
        margin: '0 auto',
      }}
    >
      <div
        style={{
          width: 96,
          height: 96,
          borderRadius: '50%',
          background: 'var(--surface-container-high)',
          border: '1px solid rgba(255,255,255,0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 'var(--sp-lg)',
          boxShadow: '0 0 40px rgba(203,32,45,0.1)',
        }}
      >
        <span
          className="material-symbols-outlined filled"
          style={{ fontSize: 48, color: 'var(--primary)' }}
        >
          search_off
        </span>
      </div>
      <h2 className="headline-lg" style={{ color: 'var(--on-surface)', marginBottom: 'var(--sp-xs)' }}>
        {title}
      </h2>
      <p className="body-md" style={{ color: 'var(--on-surface-variant)', marginBottom: 'var(--sp-lg)', lineHeight: '1.6' }}>
        {message}
      </p>
    </motion.div>
  );
};

export default EmptyState;
