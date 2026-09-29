import React from 'react';
import type { UserPreferences } from '../types';

interface Props {
  filters: UserPreferences;
}

const FilterRecap: React.FC<Props> = ({ filters }) => {
  const chips: { icon: string; text: string }[] = [
    { icon: '📍', text: filters.location },
    { icon: '💰', text: filters.budget.charAt(0).toUpperCase() + filters.budget.slice(1) },
  ];
  if (filters.cuisine) chips.push({ icon: '🍽️', text: filters.cuisine });
  if (filters.is_veg_only) chips.push({ icon: '🌱', text: 'Pure Veg' });
  if (filters.additional_preferences && filters.additional_preferences.toLowerCase().includes('halal')) {
    chips.push({ icon: '✓', text: 'Halal Friendly' });
  }
  chips.push({ icon: '⭐', text: `≥ ${filters.min_rating.toFixed(1)}` });

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {chips.map((chip, i) => (
        <span
          key={i}
          className="body-sm"
          style={{
            background: 'var(--surface-container-high)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 'var(--radius-full)',
            padding: '5px 14px',
            color: 'var(--on-surface-variant)',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 13,
          }}
        >
          {chip.icon} {chip.text}
        </span>
      ))}
    </div>
  );
};

export default FilterRecap;
