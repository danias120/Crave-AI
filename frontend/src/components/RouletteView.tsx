import React, { useState, useEffect } from 'react';
import { spinRoulette } from '../api/client';
import type { RouletteRequest, RouletteResponse } from '../types';
import './RouletteView.css';

interface Props {
  locations: string[];
}

const SHUFFLE_NAMES = [
  'Truffles',
  'Meghana Foods',
  'Corner House',
  'CTR Shri Sagar',
  'Vidyarthi Bhavan',
  'Empire Restaurant',
  'Chianti',
  'Milano Ice Cream',
  'Toit Brewpub',
  'Mavalli Tiffin Room (MTR)',
  'Glen\'s Bakehouse',
  'Leon\'s Burgers',
  'Nagarjuna',
  'The Fatty Bao',
];

const RouletteView: React.FC<Props> = ({ locations }) => {
  const [selectedLocation, setSelectedLocation] = useState('Indiranagar');
  const [budget, setBudget] = useState('');
  const [isVegOnly, setIsVegOnly] = useState(false);
  const [isHalal, setIsHalal] = useState(false);

  const [isSpinning, setIsSpinning] = useState(false);
  const [shuffleIndex, setShuffleIndex] = useState(0);
  const [winner, setWinner] = useState<RouletteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Shuffling animation effect while spinning
  useEffect(() => {
    let interval: any;
    if (isSpinning) {
      interval = setInterval(() => {
        setShuffleIndex((prev) => (prev + 1) % SHUFFLE_NAMES.length);
      }, 90);
    }
    return () => clearInterval(interval);
  }, [isSpinning]);

  const handleSpin = async () => {
    if (isSpinning) return;
    setIsSpinning(true);
    setError(null);
    setWinner(null);

    const startTime = Date.now();

    try {
      const payload: RouletteRequest = {
        location: selectedLocation || 'Indiranagar',
        budget: budget || null,
        is_veg_only: isVegOnly,
        is_halal: isHalal,
      };

      const result = await spinRoulette(payload);

      // Ensure animation spins for at least 1.5s for dramatic anticipation
      const elapsed = Date.now() - startTime;
      const delay = Math.max(0, 1600 - elapsed);

      setTimeout(() => {
        setWinner(result);
        setIsSpinning(false);
      }, delay);
    } catch (err: any) {
      setIsSpinning(false);
      setError(err?.response?.data?.detail || err.message || 'No spots matched this roulette spin');
    }
  };

  return (
    <div className="roulette-view">
      {/* Hero Header */}
      <div className="roulette-header">
        <div className="roulette-badge">
          <span className="material-symbols-outlined">casino</span>
          <span>CRAVE ROULETTE ENGINE</span>
        </div>
        <h1 className="headline-xl">
          End <span className="brand-gradient-text">Decision Paralysis</span>
        </h1>
        <p className="body-md roulette-subtitle">
          Can't decide where to eat? Set your filters, spin the wheel, and let our weighted AI algorithm pick Bangalore's best dining spot for you right now.
        </p>
      </div>

      {/* Filter Options */}
      <div className="roulette-filters-card glass-panel">
        <div className="roulette-filter-row">
          {/* Location */}
          <div className="filter-item">
            <label className="filter-lbl">
              <span className="material-symbols-outlined">location_on</span>
              <span>Neighborhood</span>
            </label>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="roulette-select"
            >
              {locations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>

          {/* Budget */}
          <div className="filter-item">
            <label className="filter-lbl">
              <span className="material-symbols-outlined">payments</span>
              <span>Budget Tier</span>
            </label>
            <select
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              className="roulette-select"
            >
              <option value="">Any Budget</option>
              <option value="low">Budget (&lt;₹500)</option>
              <option value="medium">Mid-Range (₹500-1200)</option>
              <option value="high">Fine Dining (&gt;₹1200)</option>
            </select>
          </div>

          {/* Pure Veg */}
          <label className={`roulette-toggle ${isVegOnly ? 'active' : ''}`}>
            <input
              type="checkbox"
              checked={isVegOnly}
              onChange={(e) => setIsVegOnly(e.target.checked)}
            />
            <span className="veg-og-symbol">
              <span className="veg-og-dot" />
            </span>
            <span>Pure Veg Only</span>
          </label>

          {/* Halal Friendly */}
          <label className={`roulette-toggle ${isHalal ? 'active' : ''}`}>
            <input
              type="checkbox"
              checked={isHalal}
              onChange={(e) => setIsHalal(e.target.checked)}
            />
            <span>Halal Friendly</span>
          </label>
        </div>
      </div>

      {/* The Roulette Wheel Arena */}
      <div className="roulette-arena glass-panel">
        {/* Visual Animated Spinner Wheel */}
        <div className={`roulette-wheel-box ${isSpinning ? 'spinning' : ''}`}>
          <div className="wheel-outer-ring">
            <div className="wheel-inner-hub">
              {isSpinning ? (
                <div className="shuffling-text">
                  <span className="material-symbols-outlined shuffle-icon">sync</span>
                  <h3 className="shuffle-name">{SHUFFLE_NAMES[shuffleIndex]}</h3>
                </div>
              ) : winner ? (
                <div className="winner-hub-text">
                  <span className="material-symbols-outlined star-burst">stars</span>
                  <h3 className="winner-hub-name">{winner.restaurant.name}</h3>
                </div>
              ) : (
                <div className="idle-hub-text">
                  <span className="material-symbols-outlined dice-icon">casino</span>
                  <span className="idle-prompt">READY TO SPIN</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Spin CTA */}
        <button
          type="button"
          className={`spin-action-btn ${isSpinning ? 'spinning' : ''}`}
          onClick={handleSpin}
          disabled={isSpinning}
        >
          {isSpinning ? (
            <>
              <div className="btn-spinner" />
              <span>DECIDING YOUR FATE...</span>
            </>
          ) : (
            <>
              <span className="material-symbols-outlined" style={{ fontSize: 24 }}>
                casino
              </span>
              <span>SPIN THE ROULETTE 🎲</span>
            </>
          )}
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="roulette-error glass-panel animate-fade-in-up">
          <span className="material-symbols-outlined">sentiment_dissatisfied</span>
          <p>{error}</p>
        </div>
      )}

      {/* Winner Reveal Card */}
      {!isSpinning && winner && (
        <div className="winner-reveal-card glass-panel animate-fade-in-up">
          <div className="winner-card-top">
            <div className="winner-fate-tag">
              <span className="material-symbols-outlined">auto_awesome</span>
              <span>FATE HAS SPOKEN</span>
            </div>
            <div className="winner-rating">
              <span className="material-symbols-outlined filled">star</span>
              <span>{winner.restaurant.rating.toFixed(1)}</span>
            </div>
          </div>

          <div className="winner-headline-section">
            <h2 className="winner-main-title">{winner.restaurant.name}</h2>
            <div className="winner-meta-chips">
              <span className="meta-chip">
                <span className="material-symbols-outlined">location_on</span>
                {winner.restaurant.location}
              </span>
              <span className="meta-chip">
                <span className="material-symbols-outlined">payments</span>
                {winner.restaurant.cost_for_two ? `₹${winner.restaurant.cost_for_two} for two` : winner.restaurant.budget_tier}
              </span>
              {winner.restaurant.is_veg && <span className="meta-chip veg-chip">Pure Veg</span>}
              {winner.restaurant.is_halal && <span className="meta-chip halal-chip">Halal Friendly</span>}
            </div>
          </div>

          <div className="winner-verdict-quote">
            <p className="roulette-quote">"{winner.roulette_headline}"</p>
          </div>

          {/* Intel Badges Grid */}
          <div className="intel-grid">
            {/* Must-Order Dish */}
            <div className="intel-box must-order-box">
              <div className="intel-lbl">
                <span className="material-symbols-outlined">restaurant</span>
                <span>MUST-ORDER DISH</span>
              </div>
              <p className="intel-val">{winner.must_order_dish}</p>
            </div>

            {/* Why It Won */}
            <div className="intel-box why-box">
              <div className="intel-lbl">
                <span className="material-symbols-outlined">verified</span>
                <span>WHY IT WON TONIGHT</span>
              </div>
              <p className="intel-val">{winner.why_it_won}</p>
            </div>

            {/* Pro Tip */}
            <div className="intel-box tip-box">
              <div className="intel-lbl">
                <span className="material-symbols-outlined">lightbulb</span>
                <span>INSIDER PRO TIP</span>
              </div>
              <p className="intel-val">{winner.pro_tip}</p>
            </div>
          </div>

          {/* Quick Re-spin Button */}
          <div className="respin-action-row">
            <button type="button" className="respin-btn" onClick={handleSpin}>
              <span className="material-symbols-outlined">refresh</span>
              <span>Spin Again</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RouletteView;
