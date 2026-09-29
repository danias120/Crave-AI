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
NON_VEG_WORDS = {
    "chicken", "mutton", "pork", "beef", "duck", "fish", "prawn", "prawns", "shrimp",
    "seafood", "wings", "meat", "egg", "eggs", "lamb", "bacon", "pepperoni", "ham",
    "char siu", "sea bass", "bass", "salmon", "tuna", "crab", "lobster", "squid",
    "calamari", "octopus", "anchovy", "steak", "ribs", "salami", "prosciutto",
    "turkey", "sausage", "veal", "venison"
}
NON_HALAL_WORDS = {"pork", "bacon", "ham", "beer", "cocktail", "wine", "alcohol", "lard", "char siu"}
DAIRY_WORDS = {"cheese", "paneer", "milk", "butter", "ghee", "cream", "ice cream", "curd", "yogurt", "shake", "fudge", "parmesan", "mozzarella"}

CRAVING_SYNONYMS = {
    "burger": ["burger", "sliders", "sandwich", "fries", "patty", "wrap", "fast food"],
    "pasta": ["pasta", "lasagna", "spaghetti", "penne", "alfredo", "arrabiata", "ravioli", "macaroni", "risotto", "italian"],
    "pizza": ["pizza", "woodfired", "slice", "margherita", "garlic bread", "calzone", "sourdough", "italian"],
    "italian": ["pasta", "pizza", "lasagna", "risotto", "tiramisu", "bruschetta", "ravioli"],
    "biryani": ["biryani", "pulao", "rice", "mandi", "dum biryani", "rice bowl", "mughlai", "hyderabadi"],
    "kebab": ["kebab", "tikka", "grill", "bbq", "shawarma", "tandoori", "sheekh", "seekh", "kheema", "mughlai"],
    "mughlai": ["biryani", "kebab", "butter chicken", "rogan josh", "naan", "tikka", "kheema"],
    "south indian": ["dosa", "idli", "vada", "uttapam", "sambar", "filter coffee", "thali"],
    "asian": ["ramen", "dim sum", "momo", "momos", "noodle", "noodles", "sushi", "bao", "pad thai", "fried rice"],
    "chinese": ["noodle", "noodles", "manchurian", "fried rice", "dim sum", "momos", "chilli chicken", "spring roll"],
    "healthy": ["salad", "bowl", "grain bowl", "quinoa", "smoothie", "tofu", "wrap", "avocado", "greens"],
    "vegan": ["salad", "vegan", "dairy-free", "tofu", "grain bowl", "sorbet", "hummus", "fruit bowl", "avocado"],
    "dessert": ["cheesecake", "tiramisu", "brownie", "ice cream", "fudge", "cake", "waffle", "crepe", "sundae", "pastry"],
    "sweet": ["cheesecake", "tiramisu", "brownie", "ice cream", "fudge", "cake", "waffle", "crepe", "sundae"],
    "beverage": ["craft beverage", "brew", "coffee", "shake", "mocktail", "cocktail", "smoothie", "boba", "tea", "beer"],
    "shawarma": ["shawarma", "falafel", "roll", "wrap", "hummus", "arabian"],
    "mandi": ["mandi", "biryani", "rice platter", "kabsa", "arabian"],
    "dosa": ["dosa", "benne dosa", "ghee dosa", "masala dosa", "tiffin", "south indian"],
}

CUISINE_FALLBACK_DISHES = {
    "italian": {
        "veg": "Woodfired Margherita Pizza & Creamy Penne Alfredo",
        "vegan": "Penne all'Arrabbiata & Fresh Tomato Bruschetta",
        "halal": "Smoked Chicken Pasta or BBQ Chicken Pizza",
        "any": "Woodfired Gourmet Pizza & Creamy Carbonara",
    },
    "american": {
        "veg": "Crispy Veggie & Cheese Burger with Seasoned Fries",
        "vegan": "Garden Veggie Patty Burger & Crisp Fries",
        "halal": "Crispy Grilled Chicken Burger with Hand-Cut Fries",
        "any": "All-American Gourmet Bacon/Cheeseburger & Fries",
    },
    "cafe": {
        "veg": "Gourmet Cheesy Club Sandwich & Iced Latte",
        "vegan": "Mediterranean Quinoa & Fresh Avocado Salad Bowl",
        "halal": "Grilled Chicken Panini & Artisanal Cold Brew",
        "any": "Signature Cafe Club Sandwich & Craft Shake",
    },
    "north indian": {
        "veg": "Paneer Butter Masala with Butter Garlic Naan",
        "vegan": "Dal Tadka with Steamed Basmati Rice & Roti",
        "halal": "Smoky Chicken Tikka & Fragrant Dum Biryani",
        "any": "Mughlai Butter Chicken & Tandoori Murgh",
    },
    "south indian": {
        "veg": "Crispy Ghee Masala Dosa with Sambar & Chutneys",
        "vegan": "Steamed Rice Idlis & Coconut Sambar Platter",
        "halal": "Kerala Style Chicken Roast & Parotta",
        "any": "Signature Benne Dosa & Filter Coffee",
    },
    "chinese": {
        "veg": "Veg Hakka Noodles & Steamed Veg Dim Sums",
        "vegan": "Wok-Tossed Chilli Garlic Noodles & Steamed Veg Momos",
        "halal": "Chicken Manchurian with Egg Fried Rice",
        "any": "Crispy Chilli Chicken & Wok-Tossed Hakka Noodles",
    },
    "asian": {
        "veg": "Steamed Vegetable Dim Sum & Rich Veg Ramen",
        "vegan": "Tofu & Shiitake Mushroom Pad Thai",
        "halal": "Chicken Teriyaki Rice Bowl & Steamed Gyoza",
        "any": "Authentic Tonkotsu Pork/Chicken Ramen & Gyoza",
    },
    "desserts": {
        "veg": "Signature Warm Chocolate Brownie with Hot Fudge",
        "vegan": "Fresh Seasonal Fruit Bowl & Dairy-Free Sorbet",
        "halal": "Classic Tiramisu & Rich Belgian Waffle",
        "any": "Signature Sundae & Warm Belgium Waffle",
    },
    "continental": {
        "veg": "Baked Cheesy Lasagna & Garlic Herb Toast",
        "vegan": "Grilled Herb Vegetables & Quinoa Pilaf",
        "halal": "Grilled Herb Chicken Steak with Mash & Pepper Sauce",
        "any": "Signature Grilled Steak with Sautéed Veggies",
    },
    "biryani": {
        "veg": "Hyderabadi Dum Veg Biryani with Mirchi ka Salan",
        "vegan": "Fragrant Vegetable Pulao with Fresh Mint",
        "halal": "Authentic Dum Chicken/Mutton Biryani",
        "any": "Special Hyderabadi Dum Biryani with Salan",
    },
}


def solve_group_dining_service(
    store: RestaurantStore, req: GroupDiningRequest
) -> GroupDiningResponse:
    """Find multi-cuisine restaurants that satisfy conflicting group preferences."""
    all_rests = store.get_all()
    scored_matches: List[GroupMatch] = []

    for r in all_rests:
        if req.location and not matches_location(r.location, req.location, r.address, allow_clusters=True):
            continue

        raw_dict = r.raw if isinstance(r.raw, dict) else {}
        dish_liked_raw = str(raw_dict.get("dish_liked") or "")
        dish_list = [d.strip() for d in dish_liked_raw.split(",") if d.strip()]

        cuisines_lower = [c.lower() for c in r.cuisines]
        satisfactions: List[MemberSatisfaction] = []
        satisfied_count = 0
        craving_hits = 0
        used_dishes: Set[str] = set()

        for m in req.members:
            diet = (m.diet or "").lower()
            craving = (m.craving or "").lower()

            sat = True
            dish_desc = ""

            is_pure_veg = "veg" in diet and "non" not in diet
            is_halal = "halal" in diet
            is_vegan = "vegan" in diet

            # Dietary Feasibility Check
            if is_pure_veg and not r.is_veg and not any(c in ("north indian", "south indian", "chinese", "italian", "cafe", "desserts", "bakery", "continental", "pizza", "biryani", "fast food", "beverages") for c in cuisines_lower):
                sat = False
                dish_desc = "Limited vegetarian options"
            elif is_halal and not r.is_halal:
                sat = False
                dish_desc = "Non-Halal certified"
            elif is_vegan and all(c in ("ice cream", "desserts", "bakery") for c in cuisines_lower) and not r.is_veg:
                sat = False
                dish_desc = "Limited vegan/dairy-free options"
            elif is_vegan and not any(c in ("cafe", "salads", "healthy food", "south indian", "asian", "beverages", "chinese", "italian", "continental") for c in cuisines_lower):
                sat = False
                dish_desc = "Limited vegan options"

            if sat:
                # 1. Expand craving keywords
                craving_tokens = [
                    w.strip().lower()
                    for w in craving.replace(",", " ").replace(" or ", " ").replace(" and ", " ").split()
                    if len(w.strip()) > 2
                ]
                expanded_keywords: Set[str] = set(craving_tokens)
                for tok in craving_tokens:
                    for syn_key, syn_list in CRAVING_SYNONYMS.items():
                        if syn_key in tok or tok in syn_key:
                            expanded_keywords.update(syn_list)

                # 2. Search for a distinct matching dish in dish_list
                matched_dish = None
                for dish in dish_list:
                    d_lower = dish.lower()
                    if d_lower in used_dishes:
                        continue
                    if is_pure_veg and any(nw in d_lower for nw in NON_VEG_WORDS):
                        continue
                    if is_vegan and (any(nw in d_lower for nw in NON_VEG_WORDS) or any(dw in d_lower for dw in DAIRY_WORDS)):
                        continue
                    if is_halal and any(nh in d_lower for nh in NON_HALAL_WORDS):
                        continue
                    
                    # Check if matches member's craving
                    if expanded_keywords and any(kw in d_lower for kw in expanded_keywords):
                        matched_dish = f"Specialty: {dish}"
                        used_dishes.add(d_lower)
                        craving_hits += 1
                        break

                # 3. If no craving match in dish_list, pick an unused diet-safe dish from dish_list
                if not matched_dish:
                    for dish in dish_list:
                        d_lower = dish.lower()
                        if d_lower in used_dishes:
                            continue
                        if is_pure_veg and any(nw in d_lower for nw in NON_VEG_WORDS):
                            continue
                        if is_vegan and (any(nw in d_lower for nw in NON_VEG_WORDS) or any(dw in d_lower for dw in DAIRY_WORDS)):
                            continue
                        if is_halal and any(nh in d_lower for nh in NON_HALAL_WORDS):
                            continue
                        
                        matched_dish = f"Specialty: {dish}"
                        used_dishes.add(d_lower)
                        break

                # 4. If still no dish or dish_list exhausted, use intelligent cuisine fallback
                if not matched_dish:
                    # Find matching cuisine category
                    target_cuisine = None
                    for c_key in CUISINE_FALLBACK_DISHES:
                        if c_key in cuisines_lower or any(kw in c_key for kw in expanded_keywords):
                            target_cuisine = c_key
                            break
                    if not target_cuisine and cuisines_lower:
                        target_cuisine = cuisines_lower[0]

                    diet_key = "vegan" if is_vegan else ("veg" if is_pure_veg else ("halal" if is_halal else "any"))
                    cuisine_options = CUISINE_FALLBACK_DISHES.get(target_cuisine, {})
                    dish_text = cuisine_options.get(diet_key) or cuisine_options.get("any")

                    if dish_text and dish_text.lower() not in used_dishes:
                        matched_dish = f"Can enjoy {dish_text}"
                        used_dishes.add(dish_text.lower())
                        if any(kw in dish_text.lower() for kw in expanded_keywords):
                            craving_hits += 1
                    elif craving:
                        matched_dish = f"Customizable: {m.craving.title()} option"
                    else:
                        matched_dish = f"Chef's {diet_key.title()} Selection"

                dish_desc = matched_dish
                satisfied_count += 1

            satisfactions.append(
                MemberSatisfaction(
                    member_name=m.name or "Friend",
                    satisfied=sat,
                    what_they_eat=dish_desc,
                )
            )

        total_members = max(len(req.members), 1)
        diet_score = (satisfied_count / total_members) * 100
        craving_ratio = (craving_hits / total_members) if total_members else 0.0
        
        # Quality score factors: 60% diet satisfaction, 25% craving matches, 15% restaurant rating
        combined_score = int(diet_score * 0.60 + craving_ratio * 25 + ((r.rating or 4.0) / 5.0) * 15)

        if diet_score >= 50:
            why_good = (
                f"{r.name} in {r.location} ({r.rating:.1f}★) features a versatile multi-cuisine menu "
                f"covering {', '.join(r.cuisines[:3])}, accommodating diverse dietary preferences with approx ₹{r.cost_for_two or 600} for two."
            )
            scored_matches.append(
                GroupMatch(
                    rank=0,
                    restaurant=r,
                    harmony_score=min(100, max(50, combined_score)),
                    satisfactions=satisfactions,
                    why_good_for_group=why_good,
                )
            )

    # Fallback if no spots matched
    if not scored_matches and all_rests:
        for r in all_rests[:6]:
            cuisines_lower = [c.lower() for c in r.cuisines]
            fallback_satisfactions = []
            used_fallback_dishes = set()
            for m in req.members:
                diet = (m.diet or "").lower()
                is_pure_veg = "veg" in diet and "non" not in diet
                is_vegan = "vegan" in diet
                is_halal = "halal" in diet
                diet_key = "vegan" if is_vegan else ("veg" if is_pure_veg else ("halal" if is_halal else "any"))
                
                c_key = cuisines_lower[0] if cuisines_lower else "cafe"
                dish_text = CUISINE_FALLBACK_DISHES.get(c_key, {}).get(diet_key, f"Multi-cuisine selection ({', '.join(r.cuisines[:2])})")
                fallback_satisfactions.append(
                    MemberSatisfaction(
                        member_name=m.name or "Friend",
                        satisfied=True,
                        what_they_eat=f"Specialty: {dish_text}",
                    )
                )
            scored_matches.append(
                GroupMatch(
                    rank=0,
                    restaurant=r,
                    harmony_score=85,
                    satisfactions=fallback_satisfactions,
                    why_good_for_group=f"{r.name} in {r.location} ({r.rating:.1f}★) is a recommended group dining destination.",
                )
            )

    scored_matches.sort(
        key=lambda gm: (
            gm.harmony_score,
            gm.restaurant.rating,
            gm.restaurant.votes or 0
        ),
        reverse=True,
    )
    top_matches = scored_matches[:6]
    for idx, gm in enumerate(top_matches, start=1):
        gm.rank = idx

    verdict = (
        f"Found {len(top_matches)} ideal group dining venues in {req.location} that harmonize all "
        f"{len(req.members)} members' tastes without anyone needing to compromise!"
    ) if top_matches else f"Top versatile dining spots in {req.location} suitable for your group."

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
