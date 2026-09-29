import React, { useState, useRef, useEffect } from 'react';
import type { UserPreferencesRequest } from '../types';
import './PreferenceForm.css';

interface Props {
  locations: string[];
  cuisines: string[];
  onSubmit: (prefs: UserPreferencesRequest) => void;
  isLoading: boolean;
}

const BUDGET_OPTIONS = [
  { value: 'low', label: 'Low', sub: '₹0–500' },
  { value: 'medium', label: 'Medium', sub: '₹500–1500' },
  { value: 'high', label: 'High', sub: '₹1500+' },
];

const POPULAR_CUISINES = [
  'Chinese',
  'Japanese',
  'Korean',
  'Mughlai',
  'Bakery',
  'Afghani',
  'Biryani',
  'North Indian',
  'South Indian',
  'Italian',
  'Continental',
  'Cafe',
  'Arabian',
  'African',
  'Fast Food',
  'Desserts',
  'American',
  'Asian',
  'Seafood',
  'Thai',
];

const DEFAULT_BANGALORE_LOCATIONS = [
  'BTM', 'Banashankari', 'Banaswadi', 'Bannerghatta Road', 'Basavanagudi',
  'Basaveshwara Nagar', 'Bellandur', 'Bommanahalli', 'Brigade Road', 'Brookefield',
  'CV Raman Nagar', 'Central Bangalore', 'Church Street', 'City Market', 'Commercial Street',
  'Cunningham Road', 'Domlur', 'East Bangalore', 'Ejipura', 'Electronic City',
  'Frazer Town', 'HBR Layout', 'HSR', 'Hebbal', 'Hennur', 'Hosur Road',
  'ITPL Main Road, Whitefield', 'Indiranagar', 'Infantry Road', 'JP Nagar', 'Jalahalli',
  'Jayanagar', 'Jeevan Bhima Nagar', 'KR Puram', 'Kaggadasapura', 'Kalyan Nagar',
  'Kammanahalli', 'Kanakapura Road', 'Kengeri', 'Koramangala', 'Koramangala 1st Block',
  'Koramangala 2nd Block', 'Koramangala 3rd Block', 'Koramangala 4th Block',
  'Koramangala 5th Block', 'Koramangala 6th Block', 'Koramangala 7th Block',
  'Koramangala 8th Block', 'Kumaraswamy Layout', 'Lalbagh Road', 'Langford Town',
  'Lavelle Road', 'MG Road', 'Magadi Road', 'Majestic', 'Malleshwaram',
  'Marathahalli', 'Mysore Road', 'Nagarbhavi', 'Nagawara', 'New BEL Road',
  'North Bangalore', 'Old Airport Road', 'Old Madras Road', 'Peenya', 'RT Nagar',
  'Race Course Road', 'Rajajinagar', 'Rajarajeshwari Nagar', 'Rammurthy Nagar',
  'Residency Road', 'Richmond Road', 'Richmond Town', 'Sadashiv Nagar', 'Sahakara Nagar',
  'Sanjay Nagar', 'Sankey Road', 'Sarjapur Road', 'Seshadripuram', 'Shanti Nagar',
  'Shivajinagar', 'South Bangalore', 'St. Marks Road', 'Thippasandra', 'Ulsoor',
  'Uttarahalli', 'Varthur Main Road, Whitefield', 'Vasanth Nagar', 'Vijay Nagar',
  'West Bangalore', 'Whitefield', 'Wilson Garden', 'Yelahanka', 'Yeshwantpur'
];

const PreferenceForm: React.FC<Props> = ({ locations, cuisines, onSubmit, isLoading }) => {
  const [location, setLocation] = useState('');
  const [budget, setBudget] = useState('medium');
  const [cuisine, setCuisine] = useState('');
  const [minRating, setMinRating] = useState(3.5);
  const [isVegOnly, setIsVegOnly] = useState(false);
  const [additionalPrefs, setAdditionalPrefs] = useState('');
  const [locationSearch, setLocationSearch] = useState('');
  const [cuisineSearch, setCuisineSearch] = useState('');
  const [showLocationDropdown, setShowLocationDropdown] = useState(false);
  const [showCuisineDropdown, setShowCuisineDropdown] = useState(false);
  const locationRef = useRef<HTMLDivElement>(null);
  const cuisineRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (locationRef.current && !locationRef.current.contains(e.target as Node))
        setShowLocationDropdown(false);
      if (cuisineRef.current && !cuisineRef.current.contains(e.target as Node))
        setShowCuisineDropdown(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Sorted locations in alphabetical order with fallback
  const allUniqueLocations = Array.from(
    new Set([...DEFAULT_BANGALORE_LOCATIONS, ...locations])
  ).sort((a, b) => a.localeCompare(b));

  const filteredLocations = allUniqueLocations.filter((l) =>
    l.toLowerCase().includes(locationSearch.toLowerCase())
  );

  // Combined and sorted cuisine list in alphabetical order
  const allUniqueCuisines = Array.from(
    new Set([...POPULAR_CUISINES, ...cuisines])
  ).sort((a, b) => a.localeCompare(b));

  const filteredCuisines = allUniqueCuisines.filter((c) =>
    c.toLowerCase().includes(cuisineSearch.toLowerCase())
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!location) return;
    onSubmit({
      location,
      budget,
      cuisine: cuisine || null,
      min_rating: minRating,
      additional_preferences: additionalPrefs || null,
      is_veg_only: isVegOnly,
    });
  };

  return (
    <form className="pref-form glass-panel" onSubmit={handleSubmit}>
      <h2 className="headline-lg pref-form-title">
        <span className="material-symbols-outlined filled" style={{ color: 'var(--tertiary)', fontSize: 28 }}>
          auto_awesome
        </span>
        Find Your Perfect Meal
      </h2>

      <div className="form-grid">
        {/* Location */}
        <div className="form-field" ref={locationRef}>
          <label className="label-bold">📍 Location</label>
          <div className="dropdown-wrapper">
            <input
              type="text"
              className="form-input"
              placeholder="Select your area..."
              value={showLocationDropdown ? locationSearch : location}
              onChange={(e) => {
                setLocationSearch(e.target.value);
                setShowLocationDropdown(true);
              }}
              onFocus={() => {
                setShowLocationDropdown(true);
                setLocationSearch('');
              }}
              onClick={() => {
                setShowLocationDropdown(true);
              }}
            />
            {showLocationDropdown && (
              <div className="dropdown-panel glass-panel">
                {filteredLocations.length === 0 ? (
                  <div className="dropdown-empty body-sm">No locations found</div>
                ) : (
                  filteredLocations.map((l) => (
                    <button
                      key={l}
                      type="button"
                      className={`dropdown-item body-sm ${l === location ? 'selected' : ''}`}
                      onClick={() => {
                        setLocation(l);
                        setShowLocationDropdown(false);
                        setLocationSearch('');
                      }}
                    >
                      {l}
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Budget */}
        <div className="form-field">
          <label className="label-bold">💰 Budget</label>
          <div className="budget-pills">
            {BUDGET_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                className={`budget-pill ${budget === opt.value ? 'active' : ''}`}
                onClick={() => setBudget(opt.value)}
              >
                <span className="pill-label">{opt.label}</span>
                <span className="pill-sub">{opt.sub}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Cuisine */}
        <div className="form-field" ref={cuisineRef}>
          <label className="label-bold">🍽️ Cuisine</label>
          <div className="dropdown-wrapper">
            <input
              type="text"
              className="form-input"
              placeholder="Any cuisine (Chinese, Japanese, Korean, Mughlai...)"
              value={showCuisineDropdown ? cuisineSearch : cuisine}
              onChange={(e) => {
                setCuisineSearch(e.target.value);
                setShowCuisineDropdown(true);
              }}
              onFocus={() => {
                setShowCuisineDropdown(true);
                setCuisineSearch('');
              }}
            />
            {showCuisineDropdown && (
              <div className="dropdown-panel glass-panel">
                <button
                  type="button"
                  className={`dropdown-item body-sm ${!cuisine ? 'selected' : ''}`}
                  onClick={() => {
                    setCuisine('');
                    setShowCuisineDropdown(false);
                  }}
                >
                  Any cuisine
                </button>
                {filteredCuisines.map((c) => (
                  <button
                    key={c}
                    type="button"
                    className={`dropdown-item body-sm ${c.toLowerCase() === cuisine.toLowerCase() ? 'selected' : ''}`}
                    onClick={() => {
                      setCuisine(c);
                      setShowCuisineDropdown(false);
                      setCuisineSearch('');
                    }}
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Rating */}
        <div className="form-field">
          <label className="label-bold">⭐ Minimum Rating</label>
          <div className="rating-slider-wrapper">
            <input
              type="range"
              min="0"
              max="5"
              step="0.1"
              value={minRating}
              onChange={(e) => setMinRating(parseFloat(e.target.value))}
              className="rating-slider"
            />
            <div className="rating-value">
              <span className="material-symbols-outlined filled" style={{ color: 'var(--gold)', fontSize: 18 }}>
                star
              </span>
              <span>{minRating.toFixed(1)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Veg Only Toggle */}
      <div className="form-field form-full-width veg-toggle-container">
        <div
          className={`veg-toggle-card ${isVegOnly ? 'active' : ''}`}
          onClick={() => setIsVegOnly(!isVegOnly)}
        >
          <div className="veg-toggle-left">
            <div className="veg-symbol-badge">
              <span className="veg-symbol-dot" />
            </div>
            <div className="veg-toggle-text">
              <span className="label-bold veg-toggle-label">Pure Vegetarian Only</span>
              <span className="body-sm veg-toggle-desc">Show only pure veg restaurants & cafes</span>
            </div>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={isVegOnly}
            className={`veg-switch-btn ${isVegOnly ? 'checked' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              setIsVegOnly(!isVegOnly);
            }}
          >
            <span className="veg-switch-thumb" />
          </button>
        </div>
      </div>

      {/* Additional */}
      <div className="form-field form-full-width">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
          <label className="label-bold">✏️ Additional Preferences (optional)</label>
          <div className="quick-pref-tags">
            <button
              type="button"
              className={`quick-tag ${additionalPrefs.toLowerCase().includes('halal') ? 'active' : ''}`}
              onClick={() => {
                if (additionalPrefs.toLowerCase().includes('halal')) {
                  setAdditionalPrefs(
                    additionalPrefs.replace(/halal/gi, '').replace(/,\s*,/g, ',').replace(/^,\s*|\s*,\s*$/g, '').trim()
                  );
                } else {
                  setAdditionalPrefs(additionalPrefs ? `${additionalPrefs}, halal` : 'halal');
                }
              }}
            >
              Halal Friendly
            </button>
          </div>
        </div>
        <div className="textarea-wrapper">
          <textarea
            className="form-textarea"
            placeholder="e.g., halal food, outdoor seating, rooftop, family-friendly..."
            value={additionalPrefs}
            onChange={(e) => setAdditionalPrefs(e.target.value.slice(0, 500))}
            rows={2}
          />
          <span className="char-count body-sm">{additionalPrefs.length}/500</span>
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        className="submit-btn"
        disabled={!location || isLoading}
      >
        {isLoading ? (
          <>
            <span className="material-symbols-outlined spin">progress_activity</span>
            Discovering your perfect restaurants...
          </>
        ) : (
          <>
            <span className="material-symbols-outlined">search</span>
            Get Recommendations
          </>
        )}
      </button>
    </form>
  );
};

export default PreferenceForm;
