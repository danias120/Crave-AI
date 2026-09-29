import React from 'react';
import type { ActiveTab } from '../types';
import './Header.css';

interface Props {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
}

const TABS: { id: ActiveTab; label: string; icon: string }[] = [
  { id: 'discover', label: 'Discover', icon: 'auto_awesome' },
  { id: 'dish-radar', label: 'Dish Radar', icon: 'ramen_dining' },
  { id: 'roulette', label: 'Roulette', icon: 'casino' },
  { id: 'group-dining', label: 'Group Dining', icon: 'groups' },
];

const Header: React.FC<Props> = ({ activeTab, onTabChange }) => {
  return (
    <header className="header">
      <div className="header-inner container">
        <div className="header-left">
          <a
            href="#"
            className="header-logo headline-xl brand-gradient-text"
            onClick={(e) => {
              e.preventDefault();
              onTabChange('discover');
            }}
          >
            Crave AI
          </a>
          <nav className="header-nav">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`nav-link ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => onTabChange(tab.id)}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  {tab.icon}
                </span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
