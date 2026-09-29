"""Crave AI — Streamlit Application Entrypoint.

Interactive, AI-powered food discovery engine with Discover, Dish Radar, Crave Roulette, and Group Dining solver.
"""

import os
import sys
from pathlib import Path
import streamlit as st

# Add workspace root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.store import RestaurantStore
from src.models.preferences import UserPreferences
from src.models.features import DishSearchRequest, RouletteRequest, GroupDiningRequest, GroupMember
from src.services.orchestrator import Orchestrator
from src.services.features_service import (
    search_dishes_service,
    spin_roulette_service,
    solve_group_dining_service,
)
from src.services.gemini_client import GeminiClient

# --- Page Setup ---
st.set_page_config(
    page_title="Crave AI — Bangalore Food Discovery Engine",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Dark Zomato Aesthetics ---
st.markdown(
    """
    <style>
    /* Global styling */
    .stApp {
        background-color: #131313;
        color: #e5e2e1;
    }
    
    /* Header Gradient */
    .brand-title {
        font-size: 40px;
        font-weight: 800;
        background: linear-gradient(90deg, #cb202d, #ff8a80);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .brand-tagline {
        color: #e4bdbb;
        font-size: 16px;
        margin-bottom: 24px;
    }

    /* Cards */
    .restaurant-card {
        background: #1f1f1f;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .restaurant-card:hover {
        border-color: rgba(203, 32, 45, 0.4);
    }
    .card-title {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .card-meta {
        font-size: 13px;
        color: #e4bdbb;
        margin-bottom: 8px;
    }
    .rating-pill {
        background: #234d20;
        color: #a5d6a7;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    .tag-veg {
        background: rgba(129, 199, 132, 0.15);
        color: #81c784;
        border: 1px solid rgba(129, 199, 132, 0.3);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    .tag-halal {
        background: rgba(100, 181, 246, 0.15);
        color: #64b5f6;
        border: 1px solid rgba(100, 181, 246, 0.3);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    .card-explanation {
        background: rgba(255, 255, 255, 0.04);
        border-left: 3px solid #cb202d;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 13px;
        color: #e5e2e1;
        margin-top: 10px;
        line-height: 1.4;
    }
    .ai-banner {
        background: linear-gradient(135deg, rgba(203, 32, 45, 0.15), rgba(42, 42, 42, 0.8));
        border: 1px solid rgba(203, 32, 45, 0.3);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Initialize Store & Services ---
@st.cache_resource
def get_store() -> RestaurantStore:
    return RestaurantStore()

@st.cache_resource
def get_gemini_client() -> GeminiClient:
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
    return GeminiClient(api_key=api_key)

@st.cache_resource
def get_orchestrator() -> Orchestrator:
    return Orchestrator(store=get_store(), gemini_client=get_gemini_client())

store = get_store()
locations = store.distinct_locations()
cuisines = store.distinct_cuisines()

# Popular cuisines sorted alphabetically
POPULAR_CUISINES = sorted(list(set([
    "Chinese", "Japanese", "Korean", "Mughlai", "Bakery", "Afghani",
    "Biryani", "North Indian", "South Indian", "Italian", "Continental",
    "Cafe", "Arabian", "African", "Fast Food", "Desserts", "American",
    "Asian", "Seafood", "Thai"
] + cuisines)))

# --- Header ---
st.markdown('<div class="brand-title">Crave AI</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-tagline">Your AI-Powered Bangalore Food Discovery Engine 🍽️</div>', unsafe_allow_html=True)

# --- Navigation Tabs ---
tab_discover, tab_dish, tab_roulette, tab_group = st.tabs([
    "🔍 Discover",
    "🍜 Dish Radar",
    "🎲 Crave Roulette",
    "👥 Group Dining",
])

# ==============================================================================
# TAB 1: DISCOVER (AI Food Discovery)
# ==============================================================================
with tab_discover:
    col_form, col_results = st.columns([1, 2], gap="large")

    with col_form:
        st.subheader("Preferences")
        with st.form("discover_form"):
            selected_loc = st.selectbox(
                "📍 Neighborhood",
                options=locations,
                index=locations.index("Church Street") if "Church Street" in locations else 0,
            )
            selected_budget = st.selectbox(
                "💰 Budget Tier",
                options=["low", "medium", "high"],
                format_func=lambda b: {"low": "Budget (<₹500)", "medium": "Mid-Range (₹500–1500)", "high": "Fine Dining (₹1500+)"}[b],
                index=1,
            )
            selected_cuisine = st.selectbox(
                "🍽️ Cuisine",
                options=["Any cuisine"] + POPULAR_CUISINES,
                index=0,
            )
            min_rating = st.slider("⭐ Minimum Rating", min_value=0.0, max_value=5.0, value=3.5, step=0.1)
            is_veg = st.checkbox("🌱 Pure Vegetarian Only", value=False)
            is_halal = st.checkbox("🕌 Halal Friendly", value=False)
            extra_notes = st.text_area("✏️ Additional Preferences", placeholder="e.g. cozy rooftop, outdoor seating, cold brew...", height=70)
            
            submit_discover = st.form_submit_button("Get Recommendations ✨", use_container_width=True)

    with col_results:
        if submit_discover:
            with st.spinner("Finding your perfect restaurants with Google Gemini..."):
                final_notes = extra_notes or ""
                if is_halal and "halal" not in final_notes.lower():
                    final_notes = f"{final_notes}, halal friendly".strip(", ")

                prefs = UserPreferences(
                    location=selected_loc,
                    budget=selected_budget,
                    cuisine=None if selected_cuisine == "Any cuisine" else selected_cuisine,
                    min_rating=min_rating,
                    additional_preferences=final_notes or None,
                    is_veg_only=is_veg,
                )
                orchestrator = get_orchestrator()
                res = orchestrator.recommend(prefs)

                if res.summary:
                    st.markdown(
                        f"""
                        <div class="ai-banner">
                            <strong>AI Summary:</strong> {res.summary}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if not res.recommendations:
                    st.info(f"No restaurants matched all filters in {selected_loc}. Try loosening budget or rating filters.")
                else:
                    for rec in res.recommendations:
                        r = rec.restaurant
                        veg_badge = '<span class="tag-veg">Pure Veg</span> ' if r.is_veg else ''
                        halal_badge = '<span class="tag-halal">Halal Friendly</span> ' if r.is_halal else ''
                        cost_str = f"₹{r.cost_for_two} for two" if r.cost_for_two else r.budget_tier.value

                        st.markdown(
                            f"""
                            <div class="restaurant-card">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div>
                                        <div class="card-title">#{rec.rank} {r.name}</div>
                                        <div class="card-meta">📍 {r.location} • {cost_str} • {', '.join(r.cuisines[:3])}</div>
                                    </div>
                                    <span class="rating-pill">★ {r.rating:.1f}</span>
                                </div>
                                <div style="margin-top: 6px;">
                                    {veg_badge}{halal_badge}
                                </div>
                                <div class="card-explanation">
                                    💡 <strong>Why it's recommended:</strong> {rec.explanation}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

# ==============================================================================
# TAB 2: DISH RADAR
# ==============================================================================
with tab_dish:
    st.subheader("🍜 Dish Radar Scanner")
    st.caption("Search Bangalore menus and reviews for exact dishes (Ramen, Mandi, Bingsu, Cheesecake, Dosa, Shawarma...)")

    col_q, col_loc, col_btn = st.columns([3, 2, 1])
    with col_q:
        dish_q = st.text_input("Craving / Dish", placeholder="e.g. Tonkotsu Ramen, Yemeni Mandi, Cheesecake...")
    with col_loc:
        dish_loc = st.selectbox("Location Filter", options=["All Bangalore"] + locations, index=0)
    with col_btn:
        st.write("")
        st.write("")
        scan_radar = st.button("Scan Radar 📡", use_container_width=True)

    if scan_radar and dish_q.strip():
        with st.spinner(f"Scanning Bangalore spots for '{dish_q}'..."):
            req = DishSearchRequest(
                dish_query=dish_q.strip(),
                location=None if dish_loc == "All Bangalore" else dish_loc,
                min_rating=3.5,
            )
            data = search_dishes_service(req, store)

            st.markdown(
                f"""
                <div class="ai-banner">
                    <strong>Radar Intel:</strong> {data.summary} ({data.total_matches} spots matched)
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not data.results:
                st.warning(f"No standout spots found for '{dish_q}'. Try searching a broader craving term.")
            else:
                for item in data.results:
                    r = item.restaurant
                    st.markdown(
                        f"""
                        <div class="restaurant-card">
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    <div class="card-title">#{item.rank} {r.name}</div>
                                    <div class="card-meta">📍 {r.location} • ★ {r.rating:.1f} • {r.cost_for_two or r.budget_tier}</div>
                                </div>
                                <span class="rating-pill">{item.relevance_score}% Match</span>
                            </div>
                            <div class="card-explanation">
                                🍜 <strong>Specialty Dish:</strong> {item.dish_highlight}<br/>
                                <em>Menu quote: "{item.matched_dish_text}"</em>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# ==============================================================================
# TAB 3: CRAVE ROULETTE
# ==============================================================================
with tab_roulette:
    st.subheader("🎲 Crave Roulette Engine")
    st.caption("Can't decide? Let fate and our AI pick Bangalore's best bite for you.")

    col_r_loc, col_r_veg, col_r_halal = st.columns([2, 1, 1])
    with col_r_loc:
        r_loc = st.selectbox("Roulette Neighborhood", options=locations, index=0)
    with col_r_veg:
        st.write("")
        r_veg = st.checkbox("Veg Only", value=False)
    with col_r_halal:
        st.write("")
        r_halal = st.checkbox("Halal Only", value=False)

    if st.button("SPIN THE WHEEL 🎲", type="primary", use_container_width=True):
        with st.spinner("Spinning the wheel..."):
            req = RouletteRequest(
                location=r_loc,
                is_veg_only=r_veg,
                is_halal=r_halal,
            )
            spin_res = spin_roulette_service(req, store)
            r = spin_res.restaurant

            st.balloons()
            st.markdown(
                f"""
                <div class="restaurant-card" style="border: 2px solid #cb202d; background: linear-gradient(135deg, rgba(203,32,45,0.1), rgba(31,31,31,0.9));">
                    <div style="font-size: 12px; color: #ff8a80; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 4px;">FATE HAS SPOKEN ✨</div>
                    <div class="card-title" style="font-size: 26px;">{r.name}</div>
                    <div class="card-meta">📍 {r.location} • ★ {r.rating:.1f} • {r.cost_for_two or r.budget_tier} for two</div>
                    <p style="font-style: italic; color: #ffffff; margin-top: 8px;">"{spin_res.roulette_headline}"</p>
                    <div class="card-explanation" style="border-left-color: #ffd700;">
                        🍽️ <strong>Must-Order Dish:</strong> {spin_res.must_order_dish}<br/>
                        💡 <strong>Why It Won:</strong> {spin_res.why_it_won}<br/>
                        ⭐ <strong>Insider Tip:</strong> {spin_res.pro_tip}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==============================================================================
# TAB 4: GROUP DINING SOLVER
# ==============================================================================
with tab_group:
    st.subheader("👥 Group Dining Harmony Solver")
    st.caption("Solves conflicting diets (Pure Veg, Halal, Vegan, Any) and cravings for your friend group.")

    g_loc = st.selectbox("Group Meeting Neighborhood", options=locations, index=locations.index("Church Street") if "Church Street" in locations else 0)

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("**Friend 1**")
        name1 = st.text_input("Name 1", value="Dania")
        diet1 = st.selectbox("Diet 1", ["Halal Only", "Pure Vegetarian", "Vegan", "Any", "Gluten Free"], index=0)
        crav1 = st.text_input("Craving 1", value="Smoky chicken or shawarma")

    with col_m2:
        st.markdown("**Friend 2**")
        name2 = st.text_input("Name 2", value="Rohan")
        diet2 = st.selectbox("Diet 2", ["Pure Vegetarian", "Halal Only", "Vegan", "Any", "Gluten Free"], index=0)
        crav2 = st.text_input("Craving 2", value="Crispy paneer or pasta")

    if st.button("Solve Group Dilemma 🎯", use_container_width=True):
        with st.spinner("Finding restaurants with maximum group harmony..."):
            members = [
                GroupMember(name=name1, diet=diet1, craving=crav1),
                GroupMember(name=name2, diet=diet2, craving=crav2),
            ]
            req = GroupDiningRequest(location=g_loc, members=members)
            group_res = solve_group_dining_service(req, store)

            st.markdown(
                f"""
                <div class="ai-banner">
                    <strong>Solver Verdict:</strong> {group_res.harmony_verdict}
                </div>
                """,
                unsafe_allow_html=True,
            )

            for match in group_res.recommendations:
                r = match.restaurant
                satisfactions_html = "".join([
                    f"<li><strong>{s.member_name}:</strong> {s.what_they_eat}</li>"
                    for s in match.satisfactions
                ])
                st.markdown(
                    f"""
                    <div class="restaurant-card">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <div class="card-title">#{match.rank} {r.name}</div>
                                <div class="card-meta">📍 {r.location} • ★ {r.rating:.1f} • {r.cost_for_two or r.budget_tier} for two</div>
                            </div>
                            <span class="rating-pill">{match.harmony_score}% Harmony</span>
                        </div>
                        <div class="card-explanation">
                            🤝 <strong>Group Fit:</strong> {match.why_good_for_group}
                            <ul style="margin-top: 6px; margin-bottom: 0px; padding-left: 18px;">
                                {satisfactions_html}
                            </ul>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
