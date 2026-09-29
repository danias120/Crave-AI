import axios from 'axios';
import type {
  RecommendationResponse,
  UserPreferencesRequest,
} from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

export async function getLocations(): Promise<string[]> {
  const { data } = await api.get<string[]>('/api/locations');
  return data;
}

export async function getCuisines(): Promise<string[]> {
  const { data } = await api.get<string[]>('/api/cuisines');
  return data;
}

export async function getRecommendations(
  prefs: UserPreferencesRequest
): Promise<RecommendationResponse> {
  const { data } = await api.post<RecommendationResponse>(
    '/api/recommendations',
    prefs
  );
  return data;
}

export async function getHealth(): Promise<{ status: string; restaurant_count: number }> {
  const { data } = await api.get('/api/health');
  return data;
}

// 1. Dish Radar
export async function searchDishes(req: import('../types').DishSearchRequest): Promise<import('../types').DishSearchResponse> {
  const { data } = await api.post<import('../types').DishSearchResponse>('/api/dish-search', req);
  return data;
}

// 2. Food Face-Off (Compare)
export async function compareRestaurants(req: import('../types').CompareRequest): Promise<import('../types').CompareResponse> {
  const { data } = await api.post<import('../types').CompareResponse>('/api/compare', req);
  return data;
}

// 3. Crave Roulette
export async function spinRoulette(req: import('../types').RouletteRequest): Promise<import('../types').RouletteResponse> {
  const { data } = await api.post<import('../types').RouletteResponse>('/api/roulette', req);
  return data;
}

// 4. Group Dining Solver
export async function getGroupRecommendations(req: import('../types').GroupDiningRequest): Promise<import('../types').GroupDiningResponse> {
  const { data } = await api.post<import('../types').GroupDiningResponse>('/api/group-recommendations', req);
  return data;
}

// 5. Food Trails
export async function getFoodTrails(): Promise<import('../types').FoodTrail[]> {
  const { data } = await api.get<import('../types').FoodTrail[]>('/api/trails');
  return data;
}

// Restaurant quick search for selectors
export async function searchRestaurantsQuick(query: string): Promise<import('../types').Restaurant[]> {
  const { data } = await api.get<import('../types').Restaurant[]>('/api/restaurants/search', {
    params: { q: query },
  });
  return data;
}
