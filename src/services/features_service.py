"""Services powering advanced Crave AI features: Dish Radar, Compare, Roulette, Group Dining, Trails."""

import random
from typing import Any, Dict, List, Optional
import logging

from src.data.store import RestaurantStore
from src.models.features import (
    CompareRequest,
    CompareResponse,
    CompareWinner,
    DishSearchRequest,
    DishSearchResponse,
    DishSearchResult,
    FoodTrail,
    GroupDiningRequest,
    GroupDiningResponse,
    GroupMatch,
    MemberSatisfaction,
    RouletteRequest,
    RouletteResponse,
    TrailStop,
)
from src.models.restaurant import BudgetTier, Restaurant
from src.services.filter import matches_location

logger = logging.getLogger(__name__)


# ============================================================================
# 1. DISH RADAR SERVICE
# ============================================================================
def search_dishes_service(store: RestaurantStore, req: DishSearchRequest) -> DishSearchResponse:
    """Search for restaurants specializing in a specific dish."""
    query = req.dish_query.strip().lower()
    all_rests = store.get_all()
    matches: List[DishSearchResult] = []

    for r in all_rests:
        # Check dietary constraints
        if req.is_veg_only and not r.is_veg:
            continue
        if req.is_halal and not r.is_halal:
            continue
        if req.location and not matches_location(r.location, req.location, r.address, allow_clusters=True):
            continue
        if req.budget and r.budget_tier.value.lower() != req.budget.lower():
            continue
        if r.rating < req.min_rating:
            continue

        dish_liked = (r.raw.get("dish_liked") or "").lower() if r.raw else ""
        cuisines_str = " ".join(r.cuisines).lower()
        name_lower = r.name.lower()
        rest_type = (r.raw.get("rest_type") or "").lower() if r.raw else ""

        relevance = 0.0
        matched_text = ""

        # Score relevance
        if query in dish_liked:
            relevance += 10.0
            matched_text = f"Known for: {r.raw.get('dish_liked')}"
        elif query in name_lower:
            relevance += 8.0
            matched_text = f"Specialty name: {r.name}"
        elif any(query in c.lower() or c.lower() in query for c in r.cuisines):
            relevance += 5.0
            matched_text = f"Cuisine: {', '.join(r.cuisines)}"
        elif query in rest_type:
            relevance += 4.0
            matched_text = f"Type: {r.raw.get('rest_type')}"
        else:
            continue

        # Add quality weight (rating + votes)
        relevance += r.rating * 1.5 + min(r.votes / 1000.0, 3.0)

        # Highlight
        cost_str = f"₹{r.cost_for_two} for two" if r.cost_for_two else f"{r.budget_tier.value} budget"
        highlight = f"Top-rated ({r.rating}★, {r.votes} votes) spot in {r.location} for {req.dish_query.title()} ({cost_str})."

        matches.append(
            DishSearchResult(
                rank=0,
                restaurant=r,
                matched_dish_text=matched_text,
                relevance_score=round(relevance, 2),
                dish_highlight=highlight,
            )
        )

    # Sort by relevance
    matches.sort(key=lambda m: m.relevance_score, reverse=True)
    top_matches = matches[:15]
    for idx, m in enumerate(top_matches, start=1):
        m.rank = idx

    loc_msg = f" in {req.location}" if req.location else " across Bangalore"
    summary = (
        f"Found {len(top_matches)} top restaurants serving '{req.dish_query.title()}'{loc_msg} "
        f"ranked by authentic customer ratings and dish popularity."
    ) if top_matches else f"No places specifically serving '{req.dish_query}' found{loc_msg}. Try broadening your search or location."

    return DishSearchResponse(
        dish_query=req.dish_query,
        total_matches=len(top_matches),
        summary=summary,
        results=top_matches,
    )


# ============================================================================
# 2. FOOD FACE-OFF (COMPARE)
# ============================================================================
def compare_restaurants_service(
    store: RestaurantStore, req: CompareRequest
) -> CompareResponse:
    """Perform side-by-side comparison of two restaurants."""
    r1 = store.get_by_id(req.restaurant_id_1)
    r2 = store.get_by_id(req.restaurant_id_2)

    # Fallback to search by name if ID not exact
    if not r1:
        for r in store.get_all():
            if r.name.lower() == req.restaurant_id_1.lower():
                r1 = r
                break
    if not r2:
        for r in store.get_all():
            if r.name.lower() == req.restaurant_id_2.lower():
                r2 = r
                break

    if not r1 or not r2:
        all_r = store.get_all()
        r1 = r1 or all_r[0]
        r2 = r2 or (all_r[1] if len(all_r) > 1 else all_r[0])

    winners: List[CompareWinner] = []

    # Category 1: Value for Money
    cost1 = r1.cost_for_two or 600
    cost2 = r2.cost_for_two or 600
    if cost1 < cost2:
        winners.append(CompareWinner(category="Value for Money", winner_name=r1.name, reason=f"More affordable at ~₹{cost1} for two vs ₹{cost2}."))
    elif cost2 < cost1:
        winners.append(CompareWinner(category="Value for Money", winner_name=r2.name, reason=f"More affordable at ~₹{cost2} for two vs ₹{cost1}."))
    else:
        winners.append(CompareWinner(category="Value for Money", winner_name="Tie", reason=f"Both cost approximately ₹{cost1} for two."))

    # Category 2: Popularity & Customer Love
    if (r1.votes or 0) >= (r2.votes or 0) and r1.rating >= r2.rating:
        winners.append(CompareWinner(category="Crowd Favorite", winner_name=r1.name, reason=f"Higher rating ({r1.rating}★) with {r1.votes} customer reviews."))
    elif (r2.votes or 0) >= (r1.votes or 0) and r2.rating >= r1.rating:
        winners.append(CompareWinner(category="Crowd Favorite", winner_name=r2.name, reason=f"Higher rating ({r2.rating}★) with {r2.votes} customer reviews."))
    else:
        higher_rated = r1 if r1.rating > r2.rating else r2
        winners.append(CompareWinner(category="Top Rated", winner_name=higher_rated.name, reason=f"Boasts a superior {higher_rated.rating}★ rating."))

    # Category 3: Diet & Cuisine Variety
    if len(r1.cuisines) > len(r2.cuisines):
        winners.append(CompareWinner(category="Menu Variety", winner_name=r1.name, reason=f"Offers {len(r1.cuisines)} cuisines ({', '.join(r1.cuisines)})."))
    else:
        winners.append(CompareWinner(category="Menu Variety", winner_name=r2.name, reason=f"Offers {len(r2.cuisines)} cuisines ({', '.join(r2.cuisines)})."))

    # Verdict
    recommended = r1.name if (r1.rating * 1000 + (r1.votes or 0)) >= (r2.rating * 1000 + (r2.votes or 0)) else r2.name
    verdict = (
        f"In this culinary showdown between {r1.name} and {r2.name}: {r1.name} in {r1.location} "
        f"({r1.rating}★, ₹{r1.cost_for_two or 'N/A'}) excels with specialties like {r1.raw.get('dish_liked') or 'their signature dishes'}, "
        f"while {r2.name} in {r2.location} ({r2.rating}★, ₹{r2.cost_for_two or 'N/A'}) offers standout {', '.join(r2.cuisines)}. "
        f"Pick {recommended} for the overall winning dining experience!"
    )

    return CompareResponse(
        restaurant_1=r1,
        restaurant_2=r2,
        summary_verdict=verdict,
        category_winners=winners,
        recommended_pick=recommended,
    )


# ============================================================================
# 3. CRAVE ROULETTE (SURPRISE ME)
# ============================================================================
def spin_roulette_service(store: RestaurantStore, req: RouletteRequest) -> RouletteResponse:
    """Pick a top-tier surprise restaurant matching the user's location and constraints."""
    all_rests = store.get_all()
    candidates = []

    for r in all_rests:
        if req.is_veg_only and not r.is_veg:
            continue
        if req.is_halal and not r.is_halal:
            continue
        if req.location and not matches_location(r.location, req.location, r.address, allow_clusters=True):
            continue
        if req.budget and r.budget_tier.value.lower() != req.budget.lower():
            continue
        if r.rating >= 4.0:
            candidates.append(r)

    if not candidates:
        # Relax rating
        for r in all_rests:
            if req.is_veg_only and not r.is_veg:
                continue
            if req.is_halal and not r.is_halal:
                continue
            if req.location and matches_location(r.location, req.location, r.address, allow_clusters=True):
                candidates.append(r)

    selected = random.choice(candidates) if candidates else all_rests[0]

    dishes = selected.raw.get("dish_liked") or "Chef's Daily Special"
    must_try = dishes.split(",")[0].strip() if "," in dishes else dishes

    headlines = [
        f"🎯 JackPot! You're dining at {selected.name} today!",
        f"✨ The Food Gods have spoken: {selected.name} is your calling!",
        f"🎉 Crave Winner: Experience culinary bliss at {selected.name}!",
    ]
    headline = random.choice(headlines)

    why_won = (
        f"{selected.name} in {selected.location} holds an impressive {selected.rating}★ rating "
        f"with over {selected.votes} reviews, specializing in {', '.join(selected.cuisines)}."
    )
    pro_tip = (
        f"Cost is approx ₹{selected.cost_for_two or 500} for two. "
        f"Table booking is {'recommended' if selected.raw.get('book_table') == 'Yes' else 'walk-in friendly'}!"
    )

    return RouletteResponse(
        restaurant=selected,
        roulette_headline=headline,
        why_it_won=why_won,
        must_order_dish=must_try,
        pro_tip=pro_tip,
    )


# ============================================================================
# 4. GROUP DINING SOLVER
# ============================================================================
def solve_group_dining_service(
    store: RestaurantStore, req: GroupDiningRequest
) -> GroupDiningResponse:
    """Find multi-cuisine restaurants that satisfy conflicting group preferences."""
    all_rests = store.get_all()
    scored_matches: List[GroupMatch] = []

    has_veg_member = any(m.diet.lower() == "veg" for m in req.members)
    has_halal_member = any(m.diet.lower() == "halal" for m in req.members)

    for r in all_rests:
        if not matches_location(r.location, req.location, r.address, allow_clusters=True):
            continue

        # If a member is pure veg, restaurant must have veg options (or be multi-cuisine)
        satisfactions: List[MemberSatisfaction] = []
        satisfied_count = 0

        for m in req.members:
            diet = m.diet.lower()
            craving = (m.craving or "").lower()

            sat = True
            dish_desc = ""

            if diet == "veg" and not r.is_veg and not any(c.lower() in ("north indian", "south indian", "chinese", "italian", "cafe", "desserts", "bakery") for c in r.cuisines):
                sat = False
                dish_desc = "Limited vegetarian variety"
            elif diet == "halal" and not r.is_halal:
                sat = False
                dish_desc = "Non-Halal meat source"
            else:
                if craving and any(craving in c.lower() for c in r.cuisines):
                    dish_desc = f"Serves loved {m.craving.title()} cuisine"
                elif r.raw.get("dish_liked"):
                    dish_desc = f"Can enjoy {r.raw.get('dish_liked').split(',')[0]}"
                else:
                    dish_desc = f"Great {r.cuisines[0] if r.cuisines else 'dining'} options"

            if sat:
                satisfied_count += 1

            satisfactions.append(
                MemberSatisfaction(
                    member_name=m.name,
                    satisfied=sat,
                    what_they_eat=dish_desc,
                )
            )

        harmony_score = int((satisfied_count / len(req.members)) * 100)
        # Quality boost
        quality_score = int(harmony_score * 0.7 + (r.rating / 5.0) * 30)

        if harmony_score >= 60:
            why_good = (
                f"{r.name} in {r.location} ({r.rating}★) features a versatile multi-cuisine menu "
                f"covering {', '.join(r.cuisines[:3])}, accommodating diverse dietary preferences with approx ₹{r.cost_for_two or 600} for two."
            )
            scored_matches.append(
                GroupMatch(
                    rank=0,
                    restaurant=r,
                    harmony_score=min(100, quality_score),
                    satisfactions=satisfactions,
                    why_good_for_group=why_good,
                )
            )

    scored_matches.sort(key=lambda gm: (gm.harmony_score, gm.restaurant.rating, gm.restaurant.votes or 0), reverse=True)
    top_matches = scored_matches[:6]
    for idx, gm in enumerate(top_matches, start=1):
        gm.rank = idx

    verdict = (
        f"Found {len(top_matches)} ideal group dining venues in {req.location} that harmonize all "
        f"{len(req.members)} members' tastes without anyone needing to compromise!"
    ) if top_matches else f"No single restaurant perfectly matched all group constraints in {req.location}. Consider multi-cuisine food hubs or malls."

    return GroupDiningResponse(
        location=req.location,
        total_members=len(req.members),
        harmony_verdict=verdict,
        recommendations=top_matches,
    )


# ============================================================================
# 5. BANGALORE FOOD TRAILS
# ============================================================================
CURATED_TRAILS: List[FoodTrail] = [
    FoodTrail(
        id="trail_church_street",
        title="Church Street Artisan & Cafe Crawl",
        subtitle="A cozy stroll through bookstore cafes, sourdough pizzas, artisanal bakes & Korean bingsu",
        neighborhood="Church Street",
        emoji="☕",
        duration="3 - 4 Hours",
        total_stops=4,
        highlights=["Specialty Coffee & Breads", "Sourdough Pizzeria", "Boutique Desserts", "Korean Street Food"],
        stops=[
            TrailStop(
                order=1,
                stop_name="Glen's Bakehouse",
                stop_type="Breakfast & Coffee",
                address="24/1, Lavelle Road & Church Street, Bangalore",
                rating=4.5,
                must_try="Red Velvet Cupcake & Sourdough Breakfast",
                vibe="Charming European villa cafe ambiance",
                estimated_cost="₹300 per person",
            ),
            TrailStop(
                order=2,
                stop_name="Brik Oven",
                stop_type="Lunch & Slice",
                address="Heart of Church Street, Bangalore",
                rating=4.6,
                must_try="Woodfired Sourdough Pizza & Garlic Bread",
                vibe="Bustling indie pizzeria with craft sodas",
                estimated_cost="₹400 per person",
            ),
            TrailStop(
                order=3,
                stop_name="Myeongdong Korean Street Food & Cafe",
                stop_type="Snack & Street Bites",
                address="Church Street, Near Metro Station, Bangalore",
                rating=4.4,
                must_try="Korean Cheese Corn Dog & Spicy Tteokbokki",
                vibe="K-Pop aesthetic & street-food energy",
                estimated_cost="₹200 per person",
            ),
            TrailStop(
                order=4,
                stop_name="Matteo Coffea",
                stop_type="Dessert & Pour-Over",
                address="2, Church Street, Bangalore",
                rating=4.3,
                must_try="Classic Tiramisu & Espresso Shakerato",
                vibe="Iconic outdoor seating & people watching",
                estimated_cost="₹250 per person",
            ),
        ],
    ),
    FoodTrail(
        id="trail_frazer_town",
        title="Frazer Town Legendary Halal Feast",
        subtitle="The ultimate Bangalore meat lover's trail through rich dum biryanis, kebabs, and bakeries",
        neighborhood="Frazer Town",
        emoji="🍗",
        duration="3 Hours",
        total_stops=4,
        highlights=["100% Halal Certified", "Mughlai & Biryani", "Arabian Barbecue", "Heritage Bakery"],
        stops=[
            TrailStop(
                order=1,
                stop_name="Albert Bakery",
                stop_type="Starters & Puffs",
                address="93, Mosque Road, Frazer Town, Bangalore",
                rating=4.4,
                must_try="Mutton Kheema Samosa & Coconut Biscuits",
                vibe="Century-old heritage bakery counter",
                estimated_cost="₹100 per person",
            ),
            TrailStop(
                order=2,
                stop_name="Rahhams",
                stop_type="Biryani Feast",
                address="82, MM Road, Frazer Town, Bangalore",
                rating=4.5,
                must_try="Muslim Wedding Biryani & Mutton Seekh Kebab",
                vibe="Lively dining hall with legendary aroma",
                estimated_cost="₹350 per person",
            ),
            TrailStop(
                order=3,
                stop_name="Savoury Restaurant",
                stop_type="Arabian Grill & Mandi",
                address="Mosque Road, Frazer Town, Bangalore",
                rating=4.4,
                must_try="Arabian Barbecue Chicken & Mutton Mandi",
                vibe="Spacious multi-level family restaurant",
                estimated_cost="₹350 per person",
            ),
            TrailStop(
                order=4,
                stop_name="Karama Restaurant",
                stop_type="Dessert & Kunafa",
                address="55, Mosque Road, Frazer Town, Bangalore",
                rating=4.5,
                must_try="Warm Arabic Cheese Kunafa with Ice Cream",
                vibe="Opulent Middle Eastern majlis decor",
                estimated_cost="₹200 per person",
            ),
        ],
    ),
    FoodTrail(
        id="trail_heritage_south_indian",
        title="Basavanagudi Heritage Veg Breakfast Walk",
        subtitle="Golden crispy dosas, steaming filter coffee, and iconic 80-year-old culinary institutions",
        neighborhood="Basavanagudi & Lalbagh",
        emoji="🌱",
        duration="2.5 Hours",
        total_stops=3,
        highlights=["Pure Vegetarian", "Heritage South Indian", "Iconic Filter Coffee", "Crispy Ghee Dosas"],
        stops=[
            TrailStop(
                order=1,
                stop_name="Brahmin's Coffee Bar",
                stop_type="Morning Kickoff",
                address="Ranga Rao Road, Shankarapuram, Basavanagudi, Bangalore",
                rating=4.6,
                must_try="Soft Idli Vada with Mint-Coconut Chutney & Filter Coffee",
                vibe="Standing only, bustling street corner favorite",
                estimated_cost="₹80 per person",
            ),
            TrailStop(
                order=2,
                stop_name="Vidyarthi Bhavan",
                stop_type="Legendary Dosa",
                address="32, Gandhi Bazaar Main Road, Basavanagudi, Bangalore",
                rating=4.5,
                must_try="Crispy Ghee Butter Masala Dosa",
                vibe="Vintage nostalgic dining hall lined with author portraits",
                estimated_cost="₹120 per person",
            ),
            TrailStop(
                order=3,
                stop_name="Mavalli Tiffin Room (MTR)",
                stop_type="Royal Tiffin & Sweet",
                address="14, Lalbagh Road, Mavalli, Bangalore",
                rating=4.5,
                must_try="Rava Idli with Pure Ghee & Chandrahara Sweet",
                vibe="Historic landmark eatery founded in 1924",
                estimated_cost="₹150 per person",
            ),
        ],
    ),
    FoodTrail(
        id="trail_koramangala_asian",
        title="Koramangala Pan-Asian & K-Pop Trail",
        subtitle="From authentic Korean BBQ and boba teas to steaming ramen bowls and dim sum",
        neighborhood="Koramangala",
        emoji="🥢",
        duration="3.5 Hours",
        total_stops=3,
        highlights=["Korean Fried Chicken", "Boba Tea", "Japanese Ramen", "K-Bakery Buns"],
        stops=[
            TrailStop(
                order=1,
                stop_name="K-Pocha Korean Bistro",
                stop_type="Korean Crunch & Street Bites",
                address="1st Cross, 5th Block, Koramangala, Bangalore",
                rating=4.5,
                must_try="Crispy Yangnyeom Fried Chicken & Tteokbokki",
                vibe="Neon-lit trendy Korean bistro",
                estimated_cost="₹400 per person",
            ),
            TrailStop(
                order=2,
                stop_name="Koramangala Korean Cafe & Bakery",
                stop_type="Boba & K-Pastries",
                address="5th Block, Koramangala, Bangalore",
                rating=4.4,
                must_try="Korean Garlic Cream Cheese Bun & Taro Boba",
                vibe="Minimalist pastel aesthetic cafe",
                estimated_cost="₹200 per person",
            ),
            TrailStop(
                order=3,
                stop_name="Gangnam Korean Restaurant",
                stop_type="Korean BBQ Dinner",
                address="6th Block, Koramangala, Bangalore",
                rating=4.5,
                must_try="Bulgogi Rice Bowls, Mandu & Kimchi Stew",
                vibe="Authentic tabletop barbecue dining",
                estimated_cost="₹450 per person",
            ),
        ],
    ),
]


def get_curated_trails_service() -> List[FoodTrail]:
    """Return all curated Bangalore food trails."""
    return CURATED_TRAILS
