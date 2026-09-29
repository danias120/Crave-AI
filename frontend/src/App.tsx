import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import PreferenceForm from './components/PreferenceForm';
import RecommendationCard from './components/RecommendationCard';
import ResultsSummary from './components/ResultsSummary';
import FilterRecap from './components/FilterRecap';
import EmptyState from './components/EmptyState';
import ErrorState from './components/ErrorState';
import LoadingState from './components/LoadingState';
import DishRadarView from './components/DishRadarView';
import RouletteView from './components/RouletteView';
import GroupDiningView from './components/GroupDiningView';
import Footer from './components/Footer';
import { getLocations, getCuisines, getRecommendations } from './api/client';
import type { ActiveTab, RecommendationResponse, UserPreferencesRequest } from './types';
import './App.css';

const DEFAULT_LOCATIONS = [
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

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('discover');
  const [locations, setLocations] = useState<string[]>(DEFAULT_LOCATIONS);
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [lastPrefs, setLastPrefs] = useState<UserPreferencesRequest | null>(null);

  // Load metadata on mount
  useEffect(() => {
    (async () => {
      try {
        const [locs, cuiss] = await Promise.all([getLocations(), getCuisines()]);
        setLocations(locs);
        setCuisines(cuiss);
      } catch (err) {
        console.error('Failed to load metadata:', err);
      }
    })();
  }, []);

  const handleSubmit = async (prefs: UserPreferencesRequest) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setHasSearched(true);
    setLastPrefs(prefs);

    try {
      const response = await getRecommendations(prefs);
      setResult(response);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err.message || 'Unknown error';
      setError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastPrefs) handleSubmit(lastPrefs);
  };

  const showResults = hasSearched && !isLoading;

  return (
    <div className="app">
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="main-content container">
        {/* 1. Discover Tab (Main Search Engine) */}
        {activeTab === 'discover' && (
          <>
            {!hasSearched && (
              <section className="hero-section">
                <div className="hero-glow" />
                <div className="hero-text">
                  <h1 className="headline-xl" style={{ fontSize: 48, lineHeight: '56px' }}>
                    Find exactly what you{' '}
                    <span className="brand-gradient-text">Crave</span>
                  </h1>
                  <p className="body-md" style={{ color: 'var(--on-surface-variant)', maxWidth: 500 }}>
                    Your AI-powered food discovery engine. Tell us your preferences and let Google Gemini find the perfect restaurants for you 🍽️
                  </p>
                </div>
              </section>
            )}

            <div className={`content-layout ${hasSearched ? 'two-col' : 'single-col'}`}>
              <div className={`form-section ${hasSearched ? 'sidebar' : ''}`}>
                <PreferenceForm
                  locations={locations}
                  cuisines={cuisines}
                  onSubmit={handleSubmit}
                  isLoading={isLoading}
                />
              </div>

              {hasSearched && (
                <div className="results-section">
                  {isLoading && <LoadingState />}

                  {showResults && error && (
                    <ErrorState message={error} onRetry={handleRetry} />
                  )}

                  {showResults && result && result.recommendations.length === 0 && !error && (
                    <EmptyState
                      summary={result.summary}
                      cuisine={lastPrefs?.cuisine}
                      location={lastPrefs?.location}
                    />
                  )}

                  {showResults && result && result.recommendations.length > 0 && (
                    <div className="results-content">
                      {result.meta?.filters_applied && (
                        <FilterRecap filters={result.meta.filters_applied} />
                      )}
                      {result.summary && <ResultsSummary summary={result.summary} />}
                      <div className="cards-grid">
                        {result.recommendations.map((rec, idx) => (
                          <RecommendationCard
                            key={rec.restaurant.id}
                            rec={rec}
                            index={idx}
                            isHalalSelected={Boolean(lastPrefs?.additional_preferences?.toLowerCase().includes('halal'))}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {/* 2. Dish Radar Tab */}
        {activeTab === 'dish-radar' && (
          <DishRadarView locations={locations} />
        )}

        {/* 3. Crave Roulette Tab */}
        {activeTab === 'roulette' && (
          <RouletteView locations={locations} />
        )}

        {/* 4. Group Dining Tab */}
        {activeTab === 'group-dining' && (
          <GroupDiningView locations={locations} />
        )}
      </main>

      <Footer />
    </div>
  );
};

export default App;
