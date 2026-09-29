import React, { useState } from 'react';
import { searchDishes } from '../api/client';
import type { DishSearchRequest, DishSearchResponse, DishSearchResult } from '../types';
import './DishRadarView.css';

interface Props {
  locations: string[];
}

const QUICK_DISHES = [
  { label: 'Tonkotsu Ramen', query: 'Ramen', icon: 'ramen_dining' },
  { label: 'Chicken Mandi', query: 'Mandi', icon: 'set_meal' },
  { label: 'Masala Dosa', query: 'Masala Dosa', icon: 'bakery_dining' },
  { label: 'Cheesecake', query: 'Cheesecake', icon: 'cake' },
  { label: 'Mutton Shawarma', query: 'Shawarma', icon: 'lunch_dining' },
  { label: 'Korean Bingsu', query: 'Bingsu', icon: 'icecream' },
  { label: 'Woodfired Pizza', query: 'Neapolitan Pizza', icon: 'local_pizza' },
  { label: 'Dum Biryani', query: 'Biryani', icon: 'rice_bowl' },
  { label: 'Tiramisu', query: 'Tiramisu', icon: 'cookie' },
  { label: 'Momos & Dimsum', query: 'Dimsum Momos', icon: 'soup_kitchen' },
];

const DishRadarView: React.FC<Props> = ({ locations }) => {
  const [dishQuery, setDishQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [budget, setBudget] = useState('');
  const [isVegOnly, setIsVegOnly] = useState(false);
  const [isHalal, setIsHalal] = useState(false);
  const [minRating, setMinRating] = useState<number>(3.5);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<DishSearchResponse | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (queryToUse?: string) => {
    const q = (queryToUse !== undefined ? queryToUse : dishQuery).trim();
    if (!q) return;

    if (queryToUse !== undefined) {
      setDishQuery(queryToUse);
    }

    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const payload: DishSearchRequest = {
        dish_query: q,
        location: selectedLocation || null,
        budget: budget || null,
        is_veg_only: isVegOnly,
        is_halal: isHalal,
        min_rating: minRating,
      };
      const data = await searchDishes(payload);
      setResponse(data);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err.message || 'Failed to scan dishes';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickDishClick = (query: string) => {
    setDishQuery(query);
    handleSearch(query);
  };

  return (
    <div className="dish-radar-view">
      {/* Hero Header */}
      <div className="radar-header">
        <div className="radar-badge">
          <span className="material-symbols-outlined radar-spin-icon">radar</span>
          <span>DISH RADAR SCANNER</span>
        </div>
        <h1 className="headline-xl">
          Search Bangalore by <span className="brand-gradient-text">Specific Craving</span>
        </h1>
        <p className="body-md radar-subtitle">
          Craving authentic Tonkotsu Ramen, crispy Benne Dosa, or smoked Yemeni Mandi? Dish Radar scours menus and foodie reviews to find the highest-rated masters of that exact item.
        </p>
      </div>

      {/* Search & Filter Control Card */}
      <div className="radar-control-card glass-panel">
        <form
          className="radar-search-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
        >
          <div className="radar-input-group">
            <span className="material-symbols-outlined radar-search-icon">search</span>
            <input
              type="text"
              className="radar-input"
              placeholder="What specific dish are you craving? (e.g., Tiramisu, Ramen, Mandi, Shawarma...)"
              value={dishQuery}
              onChange={(e) => setDishQuery(e.target.value)}
            />
            {dishQuery && (
              <button
                type="button"
                className="radar-clear-btn"
                onClick={() => setDishQuery('')}
                title="Clear"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            )}
            <button
              type="submit"
              className="radar-submit-btn"
              disabled={isLoading || !dishQuery.trim()}
            >
              {isLoading ? (
                <>
                  <span className="radar-spinner" />
                  <span>Scanning...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined">explore</span>
                  <span>Scan Radar</span>
                </>
              )}
            </button>
          </div>

          {/* Quick Dish Chips */}
          <div className="quick-dishes-section">
            <span className="quick-label">Trending Cravings:</span>
            <div className="quick-chips-wrapper">
              {QUICK_DISHES.map((dish) => (
                <button
                  key={dish.label}
                  type="button"
                  className={`quick-chip ${dishQuery.toLowerCase() === dish.query.toLowerCase() ? 'active' : ''}`}
                  onClick={() => handleQuickDishClick(dish.query)}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                    {dish.icon}
                  </span>
                  <span>{dish.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Advanced Filter Bar */}
          <div className="radar-filters-bar">
            {/* Location */}
            <div className="filter-pill-select">
              <span className="material-symbols-outlined">location_on</span>
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
              >
                <option value="">All Bangalore</option>
                {locations.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>

            {/* Budget */}
            <div className="filter-pill-select">
              <span className="material-symbols-outlined">payments</span>
              <select value={budget} onChange={(e) => setBudget(e.target.value)}>
                <option value="">Any Budget</option>
                <option value="low">Budget (&lt;₹500)</option>
                <option value="medium">Mid-Range (₹500-1200)</option>
                <option value="high">Fine Dining (&gt;₹1200)</option>
              </select>
            </div>

            {/* Pure Veg Toggle */}
            <label className={`filter-toggle ${isVegOnly ? 'active' : ''}`}>
              <input
                type="checkbox"
                checked={isVegOnly}
                onChange={(e) => setIsVegOnly(e.target.checked)}
              />
              <span className="veg-dot" />
              <span>Pure Veg Only</span>
            </label>

            {/* Halal Friendly Toggle */}
            <label className={`filter-toggle ${isHalal ? 'active' : ''}`}>
              <input
                type="checkbox"
                checked={isHalal}
                onChange={(e) => setIsHalal(e.target.checked)}
              />
              <span className="halal-dot" />
              <span>Halal Friendly</span>
            </label>

            {/* Rating */}
            <div className="rating-pill">
              <span className="material-symbols-outlined star-icon">star</span>
              <span>Min {minRating}★</span>
              <input
                type="range"
                min={3.0}
                max={4.8}
                step={0.1}
                value={minRating}
                onChange={(e) => setMinRating(parseFloat(e.target.value))}
                className="radar-slider"
              />
            </div>
          </div>
        </form>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="radar-loading-container animate-fade-in-up">
          <div className="radar-sonar-wrapper">
            <div className="sonar-emitter" />
            <div className="sonar-wave sonar-wave-1" />
            <div className="sonar-wave sonar-wave-2" />
            <div className="sonar-wave sonar-wave-3" />
            <span className="material-symbols-outlined sonar-center-icon">ramen_dining</span>
          </div>
          <p className="body-md" style={{ color: 'var(--on-surface-variant)', marginTop: 24 }}>
            Sweeping Bangalore menus & foodie reviews for <strong style={{ color: 'var(--primary)' }}>"{dishQuery}"</strong>...
          </p>
        </div>
      )}

      {/* Error state */}
      {!isLoading && error && (
        <div className="radar-error glass-panel animate-fade-in-up">
          <span className="material-symbols-outlined error-icon">error_outline</span>
          <p>{error}</p>
          <button className="radar-retry-btn" onClick={() => handleSearch()}>
            Try Again
          </button>
        </div>
      )}

      {/* Results presentation */}
      {!isLoading && hasSearched && response && (
        <div className="radar-results-section animate-fade-in-up">
          {/* AI Radar Summary Banner */}
          <div className="radar-summary-banner glass-panel">
            <div className="summary-top">
              <div className="matches-badge">
                <span className="material-symbols-outlined">verified</span>
                <span>{response.total_matches} Spots Found</span>
              </div>
              <span className="dish-target-tag">Target: "{response.dish_query}"</span>
            </div>
            <p className="summary-text">{response.summary}</p>
          </div>

          {/* Results List */}
          {response.results.length === 0 ? (
            <div className="radar-empty-state glass-panel">
              <span className="material-symbols-outlined empty-radar-icon">location_searching</span>
              <h3>No exact dish matches found</h3>
              <p>
                We couldn't find standout spots for "{response.dish_query}" matching all your active filters. Try loosening location, rating, or budget filters!
              </p>
            </div>
          ) : (
            <div className="radar-cards-grid">
              {response.results.map((item: DishSearchResult) => (
                <div key={item.restaurant.id} className="radar-result-card glass-panel">
                  {/* Card Top */}
                  <div className="radar-card-header">
                    <div className="radar-rank-pill">#{item.rank}</div>
                    <div className="radar-match-score">
                      <span className="material-symbols-outlined">bolt</span>
                      <span>{item.relevance_score}% Match</span>
                    </div>
                  </div>

                  {/* Restaurant Info */}
                  <div className="radar-card-body">
                    <h3 className="restaurant-title">{item.restaurant.name}</h3>
                    
                    <div className="restaurant-meta-row">
                      <span className="rating-badge">
                        <span className="material-symbols-outlined filled">star</span>
                        {item.restaurant.rating.toFixed(1)}
                      </span>
                      <span className="meta-dot">•</span>
                      <span className="meta-item">
                        <span className="material-symbols-outlined">location_on</span>
                        {item.restaurant.location}
                      </span>
                      <span className="meta-dot">•</span>
                      <span className="meta-item">
                        {item.restaurant.cost_for_two ? `₹${item.restaurant.cost_for_two} for two` : item.restaurant.budget_tier}
                      </span>
                    </div>

                    {/* Cuisines & Tags */}
                    <div className="restaurant-tags-row">
                      {item.restaurant.is_veg && <span className="tag-veg">Pure Veg</span>}
                      {item.restaurant.is_halal && <span className="tag-halal">Halal Friendly</span>}
                      {item.restaurant.cuisines.slice(0, 3).map((c) => (
                        <span key={c} className="tag-cuisine">
                          {c}
                        </span>
                      ))}
                    </div>

                    {/* Dish Radar Highlight Feature */}
                    <div className="dish-highlight-box">
                      <div className="highlight-label">
                        <span className="material-symbols-outlined">local_dining</span>
                        <span>Dish Radar Intel</span>
                      </div>
                      <p className="highlight-quote">"{item.dish_highlight}"</p>
                      {item.matched_dish_text && (
                        <div className="matched-dish-pill">
                          <span>Famous for: {item.matched_dish_text}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DishRadarView;
