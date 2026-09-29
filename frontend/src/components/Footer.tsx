import React from 'react';

const Footer: React.FC = () => (
  <footer
    style={{
      width: '100%',
      padding: 'var(--sp-md) var(--sp-lg)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      background: 'var(--surface-container-lowest)',
      borderTop: '1px solid rgba(255,255,255,0.05)',
      marginTop: 'auto',
    }}
  >
    <span className="headline-lg" style={{ fontWeight: 700, fontSize: 18, color: 'var(--on-surface)' }}>
      Crave AI
    </span>
  </footer>
);

export default Footer;
