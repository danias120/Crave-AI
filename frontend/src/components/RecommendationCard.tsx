import React from 'react';
import { motion } from 'framer-motion';
import type { Recommendation } from '../types';
import './RecommendationCard.css';

interface Props {
  rec: Recommendation;
  index: number;
  isHalalSelected?: boolean;
}

function renderStars(rating: number): string {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty);
}

function formatCost(cost: number | null): string {
  if (!cost) return 'Price N/A';
  return `₹${cost.toLocaleString('en-IN')} for two`;
}

const RecommendationCard: React.FC<Props> = ({ rec, index, isHalalSelected }) => {
  const { restaurant, explanation, rank } = rec;

  return (
    <motion.article
      className="rec-card glass-panel"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1, ease: 'easeOut' }}
    >
      {/* Rank badge */}
      <div className="rank-badge brand-gradient-bg">#{rank}</div>

      <div className="card-content">
        {/* Header row */}
        <div className="card-header">
          <div className="card-title-group">
            <h3 className="headline-lg card-name">{restaurant.name}</h3>
            {restaurant.is_veg && (
              <span className="veg-badge" title="Pure Vegetarian">
                <span className="veg-badge-dot" />
                <span>Pure Veg</span>
              </span>
            )}
            {isHalalSelected && restaurant.is_halal && (
              <span className="halal-badge" title="Halal Certified / Halal Friendly">
                <span>Halal Friendly</span>
              </span>
            )}
          </div>
          <div className="card-rating">
            <span className="material-symbols-outlined filled star-icon">star</span>
            <span className="rating-number">{restaurant.rating.toFixed(1)}</span>
          </div>
        </div>

        {/* Cuisine tags */}
        <div className="cuisine-tags">
          {restaurant.cuisines.slice(0, 4).map((c) => (
            <span key={c} className="cuisine-tag label-bold">{c}</span>
          ))}
        </div>

        {/* Meta row */}
        <div className="card-meta body-sm">
          <span className="meta-item">
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>payments</span>
            {formatCost(restaurant.cost_for_two)}
          </span>
          <span className="meta-dot" />
          <span className="meta-item">
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>location_on</span>
            {restaurant.location}
          </span>
          {restaurant.votes > 0 && (
            <>
              <span className="meta-dot" />
              <span className="meta-item">{restaurant.votes.toLocaleString()} votes</span>
            </>
          )}
        </div>

        {/* AI Explanation */}
        <div className="card-explanation">
          <p className="body-sm">{explanation}</p>
        </div>
      </div>
    </motion.article>
  );
};

export default RecommendationCard;
