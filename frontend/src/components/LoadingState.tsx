import React from 'react';

const LoadingState: React.FC = () => {
  const cards = [0, 1, 2, 3];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
      {/* Summary skeleton */}
      <div className="skeleton" style={{ height: 56, borderRadius: 'var(--radius-md)' }} />

      {/* Card skeletons */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-md)' }}>
        {cards.map((i) => (
          <div
            key={i}
            className="skeleton"
            style={{
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--sp-lg)',
              display: 'flex',
              gap: 'var(--sp-md)',
              height: 180,
            }}
          >
            {/* Rank circle */}
            <div
              style={{
                width: 36,
                height: 36,
                minWidth: 36,
                borderRadius: '50%',
                background: 'var(--surface-container-highest)',
              }}
            />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ height: 20, width: '70%', background: 'var(--surface-container-highest)', borderRadius: 4 }} />
              <div style={{ display: 'flex', gap: 6 }}>
                <div style={{ height: 16, width: 60, background: 'var(--surface-container-highest)', borderRadius: 12 }} />
                <div style={{ height: 16, width: 50, background: 'var(--surface-container-highest)', borderRadius: 12 }} />
              </div>
              <div style={{ height: 14, width: '90%', background: 'var(--surface-container-highest)', borderRadius: 4 }} />
              <div style={{ height: 14, width: '60%', background: 'var(--surface-container-highest)', borderRadius: 4 }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LoadingState;
