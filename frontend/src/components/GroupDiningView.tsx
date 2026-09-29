import React, { useState } from 'react';
import { getGroupRecommendations } from '../api/client';
import type { GroupDiningRequest, GroupDiningResponse, GroupMember } from '../types';
import './GroupDiningView.css';

interface Props {
  locations: string[];
}

const DIET_OPTIONS = [
  'Any',
  'Pure Vegetarian',
  'Vegan',
  'Halal Only',
  'Jain Friendly',
  'Gluten Free',
];

const PRESETS = [
  {
    name: 'Veggie + Halal Duo',
    location: 'Church Street',
    members: [
      { name: 'Dania', diet: 'Halal Only', craving: 'Smoky chicken or shawarma', budget_preference: 'medium' },
      { name: 'Rohan', diet: 'Pure Vegetarian', craving: 'Crispy paneer or pasta', budget_preference: 'medium' },
    ],
  },
  {
    name: 'The 4-Way Squad Dilemma',
    location: 'Indiranagar',
    members: [
      { name: 'Aarav', diet: 'Any', craving: 'Juicy burger and craft beverages', budget_preference: 'medium' },
      { name: 'Pooja', diet: 'Pure Vegetarian', craving: 'Cheesy Italian or woodfired pizza', budget_preference: 'medium' },
      { name: 'Zaid', diet: 'Halal Only', craving: 'Mughlai kebabs or biryani', budget_preference: 'medium' },
      { name: 'Kavya', diet: 'Vegan', craving: 'Healthy grain bowl or dairy-free dessert', budget_preference: 'medium' },
    ],
  },
];

const GroupDiningView: React.FC<Props> = ({ locations }) => {
  const [selectedLocation, setSelectedLocation] = useState('Church Street');
  const [members, setMembers] = useState<GroupMember[]>([
    { name: 'Friend 1', diet: 'Halal Only', craving: 'Smoky kebabs or burgers', budget_preference: 'medium' },
    { name: 'Friend 2', diet: 'Pure Vegetarian', craving: 'Paneer tikka or pasta', budget_preference: 'medium' },
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GroupDiningResponse | null>(null);

  const handleAddMember = () => {
    const num = members.length + 1;
    setMembers([
      ...members,
      { name: `Friend ${num}`, diet: 'Any', craving: '', budget_preference: 'medium' },
    ]);
  };

  const handleRemoveMember = (idx: number) => {
    if (members.length <= 2) return;
    setMembers(members.filter((_, i) => i !== idx));
  };

  const handleMemberChange = (idx: number, field: keyof GroupMember, value: string) => {
    const updated = [...members];
    updated[idx] = { ...updated[idx], [field]: value };
    setMembers(updated);
  };

  const handleApplyPreset = (preset: typeof PRESETS[0]) => {
    setSelectedLocation(preset.location);
    setMembers(preset.members);
    setResult(null);
  };

  const handleSolveGroup = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload: GroupDiningRequest = {
        location: selectedLocation,
        members: members,
      };
      const data = await getGroupRecommendations(payload);
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to solve group dining');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="group-dining-view">
      {/* Hero Header */}
      <div className="group-header">
        <div className="group-badge">
          <span className="material-symbols-outlined">groups</span>
          <span>GROUP HARMONY SOLVER</span>
        </div>
        <h1 className="headline-xl">
          End Group <span className="brand-gradient-text">Dining Disputes</span>
        </h1>
        <p className="body-md group-subtitle">
          Vegans, meat lovers, halal eaters, and picky eaters in one group? Build your crew profile and our algorithm finds Bangalore restaurants where everyone eats exceptionally well.
        </p>
      </div>

      {/* Preset Squads Bar */}
      <div className="presets-bar">
        <span className="presets-label">Quick Presets:</span>
        <div className="preset-buttons">
          {PRESETS.map((p) => (
            <button
              key={p.name}
              type="button"
              className="preset-btn"
              onClick={() => handleApplyPreset(p)}
            >
              <span className="material-symbols-outlined">group_add</span>
              <span>{p.name} ({p.members.length} people)</span>
            </button>
          ))}
        </div>
      </div>

      {/* Group Configuration Card */}
      <div className="group-builder-card glass-panel">
        <div className="builder-top-row">
          <div className="loc-selector">
            <label className="builder-lbl">
              <span className="material-symbols-outlined">location_on</span>
              <span>Meeting Neighborhood</span>
            </label>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="group-loc-select"
            >
              {locations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>

          <div className="members-count-tag">
            <span className="material-symbols-outlined">person</span>
            <span>{members.length} Friends in Group</span>
          </div>
        </div>

        {/* Member Cards Grid */}
        <div className="members-grid">
          {members.map((m, idx) => (
            <div key={idx} className="member-card">
              <div className="member-card-header">
                <div className="member-avatar">
                  <span>{m.name.charAt(0).toUpperCase() || `${idx + 1}`}</span>
                </div>
                <input
                  type="text"
                  className="member-name-input"
                  value={m.name}
                  onChange={(e) => handleMemberChange(idx, 'name', e.target.value)}
                  placeholder="Friend name"
                />
                {members.length > 2 && (
                  <button
                    type="button"
                    className="member-delete-btn"
                    onClick={() => handleRemoveMember(idx)}
                    title="Remove friend"
                  >
                    <span className="material-symbols-outlined">delete</span>
                  </button>
                )}
              </div>

              <div className="member-fields">
                <div className="field-row">
                  <label className="field-lbl">Dietary Rule:</label>
                  <select
                    value={m.diet}
                    onChange={(e) => handleMemberChange(idx, 'diet', e.target.value)}
                    className="member-diet-select"
                  >
                    {DIET_OPTIONS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="field-row">
                  <label className="field-lbl">Specific Craving:</label>
                  <input
                    type="text"
                    className="member-craving-input"
                    value={m.craving || ''}
                    onChange={(e) => handleMemberChange(idx, 'craving', e.target.value)}
                    placeholder="e.g. Pasta, spicy chicken, salad..."
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Builder Footer Actions */}
        <div className="builder-actions-row">
          <button
            type="button"
            className="add-member-btn"
            onClick={handleAddMember}
          >
            <span className="material-symbols-outlined">add</span>
            <span>Add Friend</span>
          </button>

          <button
            type="button"
            className="solve-btn"
            onClick={handleSolveGroup}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="btn-spinner" />
                <span>Finding Group Harmony...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined">check_circle</span>
                <span>Solve Group Dilemma 🎯</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="group-error glass-panel animate-fade-in-up">
          <span className="material-symbols-outlined">error_outline</span>
          <p>{error}</p>
        </div>
      )}

      {/* Results Presentation */}
      {!isLoading && result && (
        <div className="group-results-section animate-fade-in-up">
          {/* Harmony Verdict Banner */}
          <div className="harmony-banner glass-panel">
            <div className="harmony-icon-box">
              <span className="material-symbols-outlined">handshake</span>
            </div>
            <div className="harmony-info">
              <span className="harmony-subhead">SOLVER CONSENSUS</span>
              <p className="harmony-verdict-text">{result.harmony_verdict}</p>
            </div>
          </div>

          {/* Matches List */}
          <div className="group-matches-list">
            {result.recommendations.map((match) => (
              <div key={match.restaurant.id} className="group-match-card glass-panel">
                {/* Match Card Top */}
                <div className="match-header-row">
                  <div className="match-title-group">
                    <div className="match-rank-badge">#{match.rank}</div>
                    <div>
                      <h3 className="match-res-name">{match.restaurant.name}</h3>
                      <div className="match-meta-line">
                        <span className="rating-pill-sm">★ {match.restaurant.rating.toFixed(1)}</span>
                        <span>•</span>
                        <span>{match.restaurant.location}</span>
                        <span>•</span>
                        <span>{match.restaurant.cost_for_two ? `₹${match.restaurant.cost_for_two} for two` : match.restaurant.budget_tier}</span>
                      </div>
                    </div>
                  </div>

                  {/* Harmony Score Meter */}
                  <div className="harmony-meter-box">
                    <div className="harmony-percent-tag">
                      <span className="material-symbols-outlined">military_tech</span>
                      <span>{match.harmony_score}% Harmony</span>
                    </div>
                    <div className="harmony-bar-track">
                      <div
                        className="harmony-bar-fill"
                        style={{ width: `${match.harmony_score}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Why it works for the group */}
                <div className="group-why-box">
                  <span className="group-why-lbl">
                    <span className="material-symbols-outlined">recommend</span>
                    Group Fit Rationale:
                  </span>
                  <p className="group-why-text">{match.why_good_for_group}</p>
                </div>

                {/* Member-by-Member Satisfaction Breakdown */}
                <div className="member-satisfaction-grid">
                  <span className="breakdown-title">Individual Meal Plans:</span>
                  <div className="satisfaction-cards">
                    {match.satisfactions.map((sat, sIdx) => (
                      <div
                        key={sIdx}
                        className={`satisfaction-card ${sat.satisfied ? 'satisfied' : 'partial'}`}
                      >
                        <div className="sat-header">
                          <span className="sat-name">{sat.member_name}</span>
                          {sat.satisfied ? (
                            <span className="sat-status ok">
                              <span className="material-symbols-outlined">check_circle</span>
                              Satisfied
                            </span>
                          ) : (
                            <span className="sat-status partial">
                              <span className="material-symbols-outlined">info</span>
                              Customizable
                            </span>
                          )}
                        </div>
                        <p className="sat-dish">{sat.what_they_eat}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupDiningView;
