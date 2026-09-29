/* ===== Crave AI — TypeScript types mirroring backend Pydantic models ===== */

export type BudgetTier = 'low' | 'medium' | 'high';

export interface Restaurant {
  id: string;
  name: string;
  location: string;
  cuisines: string[];
  rating: number;
  cost_for_two: number | null;
  budget_tier: BudgetTier;
  address: string | null;
  votes: number;
  is_veg?: boolean;
  is_halal?: boolean;
}

export interface UserPreferencesRequest {
  location: string;
  budget: string;
  cuisine: string | null;
  min_rating: number;
  additional_preferences: string | null;
  is_veg_only?: boolean;
}

export interface Recommendation {
  rank: number;
  restaurant: Restaurant;
  explanation: string;
}

export interface UserPreferences {
  location: string;
  budget: BudgetTier;
  cuisine: string | null;
  min_rating: number;
  additional_preferences: string | null;
  is_veg_only?: boolean;
}

export interface RecommendationMeta {
  candidate_count: number;
  filters_applied: UserPreferences;
}

export interface RecommendationResponse {
  summary: string | null;
  recommendations: Recommendation[];
  meta: RecommendationMeta | null;
}

export type ActiveTab = 'discover' | 'dish-radar' | 'roulette' | 'group-dining';

// --- 1. Dish Radar ---
export interface DishSearchRequest {
  dish_query: string;
  location?: string | null;
  budget?: string | null;
  is_veg_only?: boolean;
  is_halal?: boolean;
  min_rating?: number;
}

export interface DishSearchResult {
  rank: number;
  restaurant: Restaurant;
  matched_dish_text: string;
  relevance_score: number;
  dish_highlight: string;
}

export interface DishSearchResponse {
  dish_query: string;
  total_matches: number;
  summary: string;
  results: DishSearchResult[];
}

// --- 2. Food Face-Off ---
export interface CompareRequest {
  restaurant_id_1: string;
  restaurant_id_2: string;
  occasion?: string | null;
}

export interface CompareWinner {
  category: string;
  winner_name: string;
  reason: string;
}

export interface CompareResponse {
  restaurant_1: Restaurant;
  restaurant_2: Restaurant;
  summary_verdict: string;
  category_winners: CompareWinner[];
  recommended_pick: string;
}

// --- 3. Crave Roulette ---
export interface RouletteRequest {
  location: string;
  budget?: string | null;
  is_veg_only?: boolean;
  is_halal?: boolean;
}

export interface RouletteResponse {
  restaurant: Restaurant;
  roulette_headline: string;
  why_it_won: string;
  must_order_dish: string;
  pro_tip: string;
}

// --- 4. Group Dining ---
export interface GroupMember {
  name: string;
  diet: string;
  craving?: string | null;
  budget_preference?: string | null;
}

export interface GroupDiningRequest {
  location: string;
  members: GroupMember[];
}

export interface MemberSatisfaction {
  member_name: string;
  satisfied: boolean;
  what_they_eat: string;
}

export interface GroupMatch {
  rank: number;
  restaurant: Restaurant;
  harmony_score: number;
  satisfactions: MemberSatisfaction[];
  why_good_for_group: string;
}

export interface GroupDiningResponse {
  location: string;
  total_members: number;
  harmony_verdict: string;
  recommendations: GroupMatch[];
}

// --- 5. Food Trails ---
export interface TrailStop {
  order: number;
  stop_name: string;
  restaurant_id?: string | null;
  stop_type: string;
  address: string;
  rating: number;
  must_try: string;
  vibe: string;
  estimated_cost: string;
}

export interface FoodTrail {
  id: string;
  title: string;
  subtitle: string;
  neighborhood: string;
  emoji: string;
  duration: string;
  total_stops: number;
  highlights: string[];
  stops: TrailStop[];
}
