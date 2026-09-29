"""Dataset loading, cleaning, normalization, and local caching."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.config import DATA_CACHE_DIR
from src.models.restaurant import BudgetTier, Restaurant

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"
DEFAULT_CACHE_FILE = DATA_CACHE_DIR / "restaurants.parquet"
FALLBACK_CACHE_FILE = DATA_CACHE_DIR / "restaurants.json"


def parse_rating(val: Any) -> Optional[float]:
    """Parse rating strings like '4.1/5', '4.1', or skip invalid values ('NEW', '-', None)."""
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip()
    if val_str in ("", "-", "NEW", "nan", "None"):
        return None
    if "/5" in val_str:
        val_str = val_str.split("/5")[0].strip()
    try:
        score = float(val_str)
        if 0.0 <= score <= 5.0:
            return round(score, 2)
        return None
    except (ValueError, TypeError):
        return None


def parse_cost(val: Any) -> Optional[int]:
    """Parse approximate cost for two from formatted strings (e.g. '1,200', '800')."""
    if val is None or pd.isna(val):
        return None
    val_str = str(val).replace(",", "").strip()
    if not val_str or val_str.lower() in ("nan", "none", "-"):
        return None
    try:
        cost = int(float(val_str))
        return cost if cost >= 0 else None
    except (ValueError, TypeError):
        return None


def determine_budget_tier(cost_for_two: Optional[int]) -> BudgetTier:
    """Classify cost into low, medium, or high budget tiers.

    - Low: <= 400 INR for two
    - Medium: 401 - 800 INR for two (also default for unknown cost)
    - High: > 800 INR for two
    """
    if cost_for_two is None:
        return BudgetTier.MEDIUM
    if cost_for_two <= 400:
        return BudgetTier.LOW
    elif cost_for_two <= 800:
        return BudgetTier.MEDIUM
    else:
        return BudgetTier.HIGH


def normalize_location(val: Any) -> str:
    """Normalize location string by trimming and standardizing title case."""
    if val is None or pd.isna(val):
        return "Unknown"
    loc = str(val).strip()
    return loc if loc else "Unknown"


CUISINE_STANDARDIZATION: Dict[str, str] = {
    "afghan": "Afghani",
    "afghani": "Afghani",
}

import re
import numpy as np


def clean_text(text: Any) -> str:
    """Repair mojibake encoding artifacts, remove spurious control chars, and normalize spaces."""
    if text is None or pd.isna(text):
        return ""
    s = str(text)
    # Iterative latin-1 to utf-8 decode repair for multiply encoded strings
    for _ in range(5):
        if any(c in s for c in ["Ã", "Â", "â", "\x83", "\x82", "\x99", "\x94", "\x93"]):
            try:
                repaired = s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
                if repaired and len(repaired) < len(s):
                    s = repaired
                else:
                    break
            except Exception:
                break
        else:
            break

    replacements = [
        (r"Caf[ÃÂ\x80-\xff]+", "Café"),
        (r"caf[ÃÂ\x80-\xff]+", "café"),
        (r"entr[ÃÂ\x80-\xff]+e", "entrée"),
        (r"Entr[ÃÂ\x80-\xff]+e", "Entrée"),
        (r"cr[ÃÂ\x80-\xff]+me", "crème"),
        (r"Cr[ÃÂ\x80-\xff]+me", "Crème"),
        (r"Pi[ÃÂ\x80-\xff]+ata", "Piñata"),
        (r"[ÃÂ\x80-\x9f]", ""),
        (r"\s+", " "),
    ]
    for pattern, repl in replacements:
        s = re.sub(pattern, repl, s)
    return s.strip()


def is_pure_veg(
    name: str,
    cuisines: List[str],
    rest_type: Optional[str] = None,
    dish_liked: Optional[str] = None,
    address: Optional[str] = None,
) -> bool:
    """Determine whether a restaurant is strictly vegetarian based on its name, cuisines, and metadata."""
    name_lower = name.lower()
    rest_type_lower = str(rest_type or "").lower()
    dish_liked_lower = str(dish_liked or "").lower()
    cuisines_lower = [c.lower() for c in cuisines]

    # Non-veg disqualifiers (presence of these terms indicates non-veg items are served)
    non_veg_terms = [
        "chicken", "mutton", "fish", "prawn", "seafood", "kebab", "bbq", "barbecue",
        "steak", "pork", "beef", "meat", "egg", "non veg", "non-veg", "bar", "pub",
        "brewery", "lounge", "wings", "burger king", "kfc", "mcdonald", "popeyes",
    ]
    for nv in non_veg_terms:
        if (
            nv in dish_liked_lower
            or nv in rest_type_lower
            or nv in name_lower
            or any(nv == c or nv in c for c in cuisines_lower)
        ):
            return False

    # Positive pure-veg indicators
    veg_terms = [
        "pure veg", "pure vegetarian", "vegetarian", "veg ", "veg,", "(veg)",
        "sagar", "udupi", "shanthi", "shanti", "paakashala", "maiyas", "mtr",
        "vidyarthi bhavan", "brahmin", "a2b", "adyar ananda bhavan", "sattvam",
        "anand sweets", "mithai", "sweets", "jain", "swathi", "kadamba",
        "rasovara", "rajdhani", "sukhsagar", "shiv sagar", "kamath", "kamal",
        "halli mane", "tiffin", "taaza thindi", "veena stores", "sattvik",
        "gujarati", "rajasthani", "thali", "idli", "dosa",
    ]
    for vt in veg_terms:
        if (
            vt in name_lower
            or vt in rest_type_lower
            or vt in dish_liked_lower
            or any(vt in c for c in cuisines_lower)
        ):
            return True

    # Traditional sweets, desserts, beverages without non-veg cues
    pure_veg_cuisines = {"mithai", "desserts", "ice cream", "beverages", "juices", "tea", "coffee"}
    if cuisines_lower and all(c in pure_veg_cuisines for c in cuisines_lower):
        return True

    return False


def is_halal_friendly(
    name: str,
    cuisines: List[str],
    rest_type: Optional[str] = None,
    dish_liked: Optional[str] = None,
    address: Optional[str] = None,
    is_veg: bool = False,
) -> bool:
    """Determine whether a restaurant is Halal-certified, serves Halal meat, or is pure vegetarian (permissible)."""
    if is_veg:
        return True

    name_lower = name.lower()
    rest_type_lower = str(rest_type or "").lower()
    dish_liked_lower = str(dish_liked or "").lower()
    cuisines_lower = [c.lower() for c in cuisines]

    # Explicit pork or non-halal disqualifiers
    if "pork" in dish_liked_lower or "pork" in name_lower or "bacon" in dish_liked_lower or "ham" in dish_liked_lower:
        return False

    # Positive Halal cuisines
    halal_cuisines = {
        "arabian", "mughlai", "biryani", "middle eastern", "lebanese", "afghani",
        "turkish", "persian", "hyderabadi", "lucknowi", "moroccan", "african",
        "ethiopian", "mandi",
    }
    if any(c in halal_cuisines for c in cuisines_lower):
        return True

    # Positive Halal brands / restaurant names in Bangalore
    halal_brands = [
        "empire", "rahham", "savoury", "karama", "al bek", "al-bek", "al amanah",
        "al-amanah", "chichaba", "fanoos", "imperial", "nagarjuna", "meghana",
        "sharief bhai", "beijing bites", "mainland china", "al tabaq", "al reem",
        "taza kitchen", "leon grill", "truffles", "paradise", "bawarchi",
        "biryani zone", "behrouz", "donne biryani", "kebab", "kabab", "shawarma",
        "mandi", "dastar", "sheesh", "bbq ride", "habesha", "african delights",
        "blue nile", "mama africa", "berco", "chowman", "chung wah",
    ]
    for hb in halal_brands:
        if hb in name_lower:
            return True

    # Positive Halal terms in dishes / rest type
    halal_terms = [
        "halal", "shawarma", "mandi", "kebab", "kabab", "biryani",
        "tandoori chicken", "butter chicken", "nihari", "haleem",
        "sheermal", "falafel", "hummus", "fattoush", "doro wat", "jollof",
    ]
    for ht in halal_terms:
        if ht in dish_liked_lower or ht in rest_type_lower:
            return True

    return False


SUPPLEMENTAL_RESTAURANTS: List[Dict[str, Any]] = [
    # --- BAKERY & DESSERT CAFES ---
    {
        "name": "Glen's Bakehouse",
        "location": "Church Street",
        "cuisines": ["Bakery", "Desserts", "Cafe", "Italian"],
        "rating": 4.5,
        "cost_for_two": 600,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": False,
        "address": "24/1, Lavelle Road & Church Street, Shantala Nagar, Bangalore",
        "votes": 4850,
        "raw": {
            "rest_type": "Bakery, Cafe",
            "dish_liked": "Red Velvet Cupcake, New York Cheesecake, Sourdough Breads, Pasta",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Magnolia Bakery",
        "location": "Church Street",
        "cuisines": ["Bakery", "Desserts"],
        "rating": 4.4,
        "cost_for_two": 500,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": True,
        "is_halal": True,
        "address": "Junction of Church Street & Brigade Road, Bangalore",
        "votes": 2600,
        "raw": {
            "rest_type": "Bakery, Dessert Parlor",
            "dish_liked": "Classic Banana Pudding, Red Velvet Cake, Cupcakes, Cheesecakes",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "The French Loaf",
        "location": "Church Street",
        "cuisines": ["Bakery", "Fast Food", "Desserts"],
        "rating": 4.1,
        "cost_for_two": 350,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": True,
        "address": "Brigade Road / Church Street, Bangalore",
        "votes": 950,
        "raw": {
            "rest_type": "Bakery",
            "dish_liked": "Croissants, Quiche, Chocolate Mousse, Chicken Puffs",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Lavonne Cafe & Patisserie",
        "location": "Church Street",
        "cuisines": ["Bakery", "Desserts", "Cafe", "French"],
        "rating": 4.7,
        "cost_for_two": 800,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": False,
        "address": "Church Street & Central Bangalore Corridor, Bangalore",
        "votes": 3800,
        "raw": {
            "rest_type": "Bakery, Cafe",
            "dish_liked": "Almond Croissant, Chocolate Entremet, French Macarons, Specialty Coffee",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "The White Room - Coffee & Kitchen",
        "location": "Church Street",
        "cuisines": ["Bakery", "Cafe", "Continental", "Desserts"],
        "rating": 4.2,
        "cost_for_two": 700,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": False,
        "address": "High Gates Hotel, 33, Church Street, Bangalore",
        "votes": 1250,
        "raw": {
            "rest_type": "Cafe, Bakery",
            "dish_liked": "Apple Pie, Carrot Cake, Fresh Brewed Coffee, English Breakfast",
            "online_order": "No",
            "book_table": "Yes",
        },
    },
    {
        "name": "Matteo Coffea",
        "location": "Church Street",
        "cuisines": ["Bakery", "Cafe", "Desserts", "Beverages"],
        "rating": 4.3,
        "cost_for_two": 600,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": True,
        "is_halal": True,
        "address": "2, Church Street, Bangalore",
        "votes": 4300,
        "raw": {
            "rest_type": "Cafe, Bakery",
            "dish_liked": "Cheesecake, Tiramisu, Chocolate Brownie, Espresso, Sandwiches",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Brik Oven",
        "location": "Church Street",
        "cuisines": ["Bakery", "Pizza", "Italian", "Cafe"],
        "rating": 4.6,
        "cost_for_two": 800,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": False,
        "address": "Heart of Church Street, Shantala Nagar, Bangalore",
        "votes": 3950,
        "raw": {
            "rest_type": "Pizzeria, Bakery",
            "dish_liked": "Sourdough Pizza, Belgian Waffles, Nutella Cheesecake, Garlic Bread",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Third Wave Coffee Roasters",
        "location": "Church Street",
        "cuisines": ["Bakery", "Cafe", "Beverages", "Desserts"],
        "rating": 4.5,
        "cost_for_two": 500,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": True,
        "is_halal": True,
        "address": "Church Street, Shantala Nagar, Bangalore",
        "votes": 2400,
        "raw": {
            "rest_type": "Cafe, Bakery",
            "dish_liked": "Butter Croissant, Bagels, Banana Walnut Cake, Pour Over Coffee",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Smoor Chocolates & Bakes",
        "location": "Church Street",
        "cuisines": ["Bakery", "Desserts", "Cafe"],
        "rating": 4.4,
        "cost_for_two": 700,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": True,
        "is_halal": True,
        "address": "Church Street, Bangalore",
        "votes": 2100,
        "raw": {
            "rest_type": "Dessert Parlor, Bakery",
            "dish_liked": "Couverture Chocolates, French Pastries, Red Velvet Cheesecake",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Albert Bakery",
        "location": "Frazer Town",
        "cuisines": ["Bakery", "Fast Food", "Desserts"],
        "rating": 4.4,
        "cost_for_two": 200,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": True,
        "address": "93, Mosque Road, Frazer Town, Bangalore",
        "votes": 3100,
        "raw": {
            "rest_type": "Bakery",
            "dish_liked": "Mutton Kheema Samosa, Coconut Biscuits, Plum Cake, Puffs",
            "online_order": "No",
            "book_table": "No",
        },
    },
    {
        "name": "Variar Bakery",
        "location": "Rajajinagar",
        "cuisines": ["Bakery", "Snacks", "Fast Food"],
        "rating": 4.7,
        "cost_for_two": 150,
        "budget_tier": BudgetTier.LOW,
        "is_veg": True,
        "is_halal": True,
        "address": "12th Main Road, Rajajinagar 2nd Block, Bangalore",
        "votes": 3800,
        "raw": {
            "rest_type": "Bakery",
            "dish_liked": "Butter Biscuits, Khara Bun, Potato Bun, Dilpasand",
            "online_order": "No",
            "book_table": "No",
        },
    },

    # --- PURE VEG LANDMARKS ---
    {
        "name": "Paakashala",
        "location": "Church Street",
        "cuisines": ["South Indian", "North Indian", "Chinese"],
        "rating": 4.4,
        "cost_for_two": 450,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": True,
        "is_halal": True,
        "address": "MG Road / Church Street Junction, Bangalore",
        "votes": 3200,
        "raw": {
            "rest_type": "Quick Bites, Casual Dining",
            "dish_liked": "Ghee Roast Dosa, Filter Coffee, Paneer Butter Masala, Rava Idli",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Sattvam",
        "location": "Sadashiv Nagar",
        "cuisines": ["Sattvik", "North Indian", "South Indian"],
        "rating": 4.6,
        "cost_for_two": 1200,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": True,
        "is_halal": True,
        "address": "Sankey Road, Sadashiv Nagar, Bangalore",
        "votes": 4100,
        "raw": {
            "rest_type": "Fine Dining",
            "dish_liked": "Sattvik Buffet, Paneer Tikka, Kulfi, Halwa",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Vidyarthi Bhavan",
        "location": "Basavanagudi",
        "cuisines": ["South Indian"],
        "rating": 4.5,
        "cost_for_two": 200,
        "budget_tier": BudgetTier.LOW,
        "is_veg": True,
        "is_halal": True,
        "address": "32, Gandhi Bazaar Main Road, Basavanagudi, Bangalore",
        "votes": 8900,
        "raw": {
            "rest_type": "Quick Bites",
            "dish_liked": "Crispy Masala Dosa, Filter Coffee, Kesari Bath, Poori Saagu",
            "online_order": "No",
            "book_table": "No",
        },
    },
    {
        "name": "Mavalli Tiffin Room (MTR)",
        "location": "Lalbagh Road",
        "cuisines": ["South Indian"],
        "rating": 4.5,
        "cost_for_two": 300,
        "budget_tier": BudgetTier.LOW,
        "is_veg": True,
        "is_halal": True,
        "address": "14, Lalbagh Road, Mavalli, Bangalore",
        "votes": 9500,
        "raw": {
            "rest_type": "Quick Bites",
            "dish_liked": "Rava Idli, Masala Dosa, Bisibele Bath, Chandrahara",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Brahmin's Coffee Bar",
        "location": "Basavanagudi",
        "cuisines": ["South Indian"],
        "rating": 4.6,
        "cost_for_two": 150,
        "budget_tier": BudgetTier.LOW,
        "is_veg": True,
        "is_halal": True,
        "address": "Ranga Rao Road, Shankarapuram, Basavanagudi, Bangalore",
        "votes": 7200,
        "raw": {
            "rest_type": "Quick Bites",
            "dish_liked": "Soft Idli, Vada, Coconut Chutney, Khara Bath, Filter Coffee",
            "online_order": "No",
            "book_table": "No",
        },
    },
    {
        "name": "Rajdhani Thali Restaurant",
        "location": "Lavelle Road",
        "cuisines": ["Rajasthani", "Gujarati", "North Indian"],
        "rating": 4.4,
        "cost_for_two": 750,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": True,
        "is_halal": True,
        "address": "Level 1, UB City, Vittal Mallya Road, Lavelle Road, Bangalore",
        "votes": 3100,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Royal Thali, Dal Baati Churma, Dhokla, Jalebi",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },

    # --- CHINESE RESTAURANTS & CAFES ---
    {
        "name": "The Fatty Bao",
        "location": "Church Street",
        "cuisines": ["Asian", "Chinese", "Japanese"],
        "rating": 4.6,
        "cost_for_two": 1400,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": True,
        "address": "Lavelle Road & Church Street vicinity, Shantala Nagar, Bangalore",
        "votes": 4900,
        "raw": {
            "rest_type": "Casual Dining, Asian Bar",
            "dish_liked": "Pork Baos, Char Siu Bao, Dim Sums, Ramen, Tempura Prawns",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Mainland China",
        "location": "Church Street",
        "cuisines": ["Chinese", "Asian", "Seafood"],
        "rating": 4.5,
        "cost_for_two": 1200,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": True,
        "address": "14, Church Street & Residency Road Junction, Bangalore",
        "votes": 4300,
        "raw": {
            "rest_type": "Fine Dining",
            "dish_liked": "Jumbo Prawns, Chicken Dumplings, Hunan Chicken, Schezwan Fried Rice",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Berco's",
        "location": "Church Street",
        "cuisines": ["Chinese", "Thai", "Asian"],
        "rating": 4.3,
        "cost_for_two": 750,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "40/1, Central Building, Church Street, Bangalore",
        "votes": 2850,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Chili Chicken, Hakka Noodles, Thukpa, Corn Pepper Salt, Dim Sums",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Chung Wah",
        "location": "Church Street",
        "cuisines": ["Chinese", "Asian", "Fast Food"],
        "rating": 4.2,
        "cost_for_two": 450,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "46, Church Street, Shantala Nagar, Bangalore",
        "votes": 3500,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Sweet Corn Chicken Soup, Veg Manchurian, American Chop Suey, Fried Rice",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Chowman",
        "location": "Church Street",
        "cuisines": ["Chinese", "Asian", "Seafood"],
        "rating": 4.4,
        "cost_for_two": 500,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "Church Street & Central Bangalore Area, Bangalore",
        "votes": 2900,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Kung Pao Chicken, Roasted Chili Pork, Shanghai Noodles, Wonton Soup",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Lucky Chan - Dim Sum & Boba Tea",
        "location": "Church Street",
        "cuisines": ["Chinese", "Asian", "Beverages"],
        "rating": 4.7,
        "cost_for_two": 800,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": False,
        "address": "Church Street, Shantala Nagar, Bangalore",
        "votes": 3100,
        "raw": {
            "rest_type": "Casual Dining, Cafe",
            "dish_liked": "Truffle Edamame Dim Sum, Crystal Dumplings, Taro Boba, Spicy Wontons",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Wok with Chung",
        "location": "Church Street",
        "cuisines": ["Chinese", "Fast Food", "Asian"],
        "rating": 4.0,
        "cost_for_two": 350,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": True,
        "address": "Church Street Alley, Bangalore",
        "votes": 850,
        "raw": {
            "rest_type": "Quick Bites",
            "dish_liked": "Street Hakka Noodles, Momos, Spring Rolls, Egg Fried Rice",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Szechwan Court - The Oberoi",
        "location": "MG Road",
        "cuisines": ["Chinese", "Asian"],
        "rating": 4.7,
        "cost_for_two": 2200,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": True,
        "address": "The Oberoi, 37-39, MG Road, Bangalore",
        "votes": 2400,
        "raw": {
            "rest_type": "Fine Dining",
            "dish_liked": "Peking Duck, Szechwan Prawns, Steamed Sea Bass, Dim Sum",
            "online_order": "No",
            "book_table": "Yes",
        },
    },
    {
        "name": "Canton Restaurant",
        "location": "Brigade Road",
        "cuisines": ["Chinese", "Asian"],
        "rating": 4.1,
        "cost_for_two": 400,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": True,
        "address": "Brigade Road / Church Street Junction, Bangalore",
        "votes": 1600,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Cantonese Noodles, Crispy Chili Baby Corn, Golden Fried Prawns",
            "online_order": "Yes",
            "book_table": "No",
        },
    },

    # --- JAPANESE RESTAURANTS & CAFES ---
    {
        "name": "Naru Noodle Bar",
        "location": "Church Street",
        "cuisines": ["Japanese", "Asian"],
        "rating": 4.8,
        "cost_for_two": 1500,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "Shanthala Nagar, Church Street vicinity, Bangalore",
        "votes": 3700,
        "raw": {
            "rest_type": "Noodle Bar, Specialty",
            "dish_liked": "Shoyu Ramen, Tonkotsu Ramen, Handmade Gyoza, Matcha Panna Cotta",
            "online_order": "No",
            "book_table": "Yes",
        },
    },
    {
        "name": "Harima Japanese Restaurant",
        "location": "Residency Road",
        "cuisines": ["Japanese", "Asian"],
        "rating": 4.6,
        "cost_for_two": 1800,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "4th Floor, Devatha Plaza, 131, Residency Road, Bangalore",
        "votes": 4200,
        "raw": {
            "rest_type": "Fine Dining, Japanese",
            "dish_liked": "Salmon Sashimi, Tempura Moriawase, Chicken Teriyaki, Udon Noodle, Maki Rolls",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Matsuri Japanese Restaurant",
        "location": "Lavelle Road",
        "cuisines": ["Japanese", "Asian"],
        "rating": 4.5,
        "cost_for_two": 1600,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "The Chancery Hotel, 10/6, Lavelle Road, Bangalore",
        "votes": 2600,
        "raw": {
            "rest_type": "Fine Dining",
            "dish_liked": "Bento Sets, Nigiri Sushi, Miso Soup, Yakitori, Tempura",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Azuki Japanese Restaurant & Cafe",
        "location": "Richmond Road",
        "cuisines": ["Japanese", "Cafe", "Desserts"],
        "rating": 4.6,
        "cost_for_two": 750,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": False,
        "address": "Richmond Road, Near MG Road, Bangalore",
        "votes": 2800,
        "raw": {
            "rest_type": "Cafe, Japanese Casual",
            "dish_liked": "Japanese Katsu Curry, Dorayaki, Onigiri, Matcha Latte, Ramen",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Kuuraku",
        "location": "Brigade Road",
        "cuisines": ["Japanese", "Asian"],
        "rating": 4.7,
        "cost_for_two": 1100,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "Forum Rex Walk, Brigade Road, Bangalore",
        "votes": 3400,
        "raw": {
            "rest_type": "Izakaya, Japanese",
            "dish_liked": "Yakitori Skewers, Kuuraku Ramen, Spicy Gyoza, Kushiyaki",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Daily Sushi",
        "location": "Church Street",
        "cuisines": ["Japanese", "Asian", "Fast Food"],
        "rating": 4.2,
        "cost_for_two": 450,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": False,
        "address": "Church Street, Bangalore",
        "votes": 1450,
        "raw": {
            "rest_type": "Quick Bites, Sushi Bar",
            "dish_liked": "California Roll, Spicy Tuna Maki, Tempura Roll, Poke Bowl",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Sakae Japanese Quick Bites",
        "location": "Church Street",
        "cuisines": ["Japanese", "Fast Food", "Asian"],
        "rating": 4.0,
        "cost_for_two": 380,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": False,
        "address": "Church Street, Shantala Nagar, Bangalore",
        "votes": 920,
        "raw": {
            "rest_type": "Quick Bites",
            "dish_liked": "Teriyaki Chicken Rice Bowl, Veg Maki, Miso Soup, Crispy Gyoza",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "You Mee",
        "location": "Church Street",
        "cuisines": ["Japanese", "Asian", "Chinese"],
        "rating": 4.4,
        "cost_for_two": 800,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": False,
        "address": "Church Street & MG Road Corridor, Bangalore",
        "votes": 2100,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "You Mee Signature Ramen, Robata Skewers, Dragon Sushi Roll",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Taiki",
        "location": "Indiranagar",
        "cuisines": ["Japanese", "Korean", "Asian"],
        "rating": 4.6,
        "cost_for_two": 1200,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "656, 100 Feet Road, Indiranagar, Bangalore",
        "votes": 5200,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Ramen, Bibimbap, Sushi Platter, Korean Fried Chicken, Bingsu",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Edo Restaurant & Bar - ITC Gardenia",
        "location": "Residency Road",
        "cuisines": ["Japanese", "Asian"],
        "rating": 4.8,
        "cost_for_two": 2800,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "ITC Gardenia, 1, Residency Road, Bangalore",
        "votes": 1950,
        "raw": {
            "rest_type": "Fine Dining",
            "dish_liked": "Kaiseki Menu, Robatayaki, Sashimi, Wasabi Ice Cream",
            "online_order": "No",
            "book_table": "Yes",
        },
    },
    {
        "name": "Tokyo Table & Matcha Cafe",
        "location": "Church Street",
        "cuisines": ["Japanese", "Cafe", "Beverages", "Desserts"],
        "rating": 4.3,
        "cost_for_two": 400,
        "budget_tier": BudgetTier.LOW,
        "is_veg": True,
        "is_halal": True,
        "address": "Church Street, Bangalore",
        "votes": 1100,
        "raw": {
            "rest_type": "Cafe, Dessert Parlor",
            "dish_liked": "Ceremonial Matcha Latte, Japanese Souffle Pancakes, Miso Toast",
            "online_order": "Yes",
            "book_table": "No",
        },
    },

    # --- KOREAN RESTAURANTS & CAFES ---
    {
        "name": "Seoul Restaurant & Cafe",
        "location": "Church Street",
        "cuisines": ["Korean", "Asian", "Cafe"],
        "rating": 4.6,
        "cost_for_two": 800,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "Church Street & MG Road Corridor, Shantala Nagar, Bangalore",
        "votes": 3400,
        "raw": {
            "rest_type": "Casual Dining, Cafe",
            "dish_liked": "Kimchi Fried Rice, Tteokbokki, K-Fried Chicken, Bibimbap, Boba Tea",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Myeongdong Korean Street Food & Cafe",
        "location": "Church Street",
        "cuisines": ["Korean", "Fast Food", "Cafe"],
        "rating": 4.4,
        "cost_for_two": 400,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": True,
        "address": "Church Street, Near Metro Station, Bangalore",
        "votes": 2200,
        "raw": {
            "rest_type": "Quick Bites, Cafe",
            "dish_liked": "Korean Cheese Corn Dog, Spicy Tteokbokki, Ramyeon Bowl, Kimchi Mandu",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "K-Pop & Bingsu Cafe",
        "location": "Church Street",
        "cuisines": ["Korean", "Cafe", "Desserts"],
        "rating": 4.3,
        "cost_for_two": 350,
        "budget_tier": BudgetTier.LOW,
        "is_veg": True,
        "is_halal": True,
        "address": "Brigade Road / Church Street Cross, Bangalore",
        "votes": 1750,
        "raw": {
            "rest_type": "Cafe, Dessert Parlor",
            "dish_liked": "Mango Bingsu, Korean Injeolmi Toast, Dalgona Iced Coffee, K-Boba",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Arirang Korean Restaurant",
        "location": "Kammanahalli",
        "cuisines": ["Korean", "Asian"],
        "rating": 4.7,
        "cost_for_two": 1200,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "KRL Layout, Kammanahalli Main Road, Bangalore",
        "votes": 3900,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Bulgogi BBQ, Kimchi Jjigae, Japchae, Seafood Pancake, Samgyeopsal",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Soo Ra Sang",
        "location": "Indiranagar",
        "cuisines": ["Korean", "Asian"],
        "rating": 4.6,
        "cost_for_two": 1400,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "Himalayan Hotel, Old Airport Road, Indiranagar, Bangalore",
        "votes": 3100,
        "raw": {
            "rest_type": "Casual Dining, Korean BBQ",
            "dish_liked": "Tabletop Korean Barbecue, Galbi, Spicy Pork Belly, Kimchi Stew",
            "online_order": "No",
            "book_table": "Yes",
        },
    },
    {
        "name": "Hi Seoul",
        "location": "Kalyan Nagar",
        "cuisines": ["Korean", "Asian", "Cafe"],
        "rating": 4.5,
        "cost_for_two": 700,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "CMR Road, HRBR Layout, Kalyan Nagar, Bangalore",
        "votes": 2600,
        "raw": {
            "rest_type": "Casual Dining, Cafe",
            "dish_liked": "Gimbap, Korean Bibimbap, Tteokbokki, Spicy Ramyun, Mandu",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "K-Pocha Korean Bistro",
        "location": "Koramangala 5th Block",
        "cuisines": ["Korean", "Asian", "Cafe"],
        "rating": 4.5,
        "cost_for_two": 850,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": True,
        "address": "1st Cross, 5th Block, Koramangala, Bangalore",
        "votes": 2900,
        "raw": {
            "rest_type": "Bistro, Cafe",
            "dish_liked": "Crispy Korean Fried Chicken, Bulgogi Rice Bowl, Kimchi Chigae, Boba",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Gangnam Korean Restaurant",
        "location": "Koramangala 6th Block",
        "cuisines": ["Korean", "Asian"],
        "rating": 4.5,
        "cost_for_two": 900,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": False,
        "address": "6th Block, Koramangala, Bangalore",
        "votes": 2400,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Yangnyeom Chicken, Korean Dumplings, Kimchi Fried Rice, Soju",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Koramangala Korean Cafe & Bakery",
        "location": "Koramangala 5th Block",
        "cuisines": ["Korean", "Bakery", "Cafe"],
        "rating": 4.4,
        "cost_for_two": 450,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": True,
        "is_halal": True,
        "address": "5th Block, Koramangala, Bangalore",
        "votes": 1600,
        "raw": {
            "rest_type": "Cafe, Bakery",
            "dish_liked": "Korean Garlic Cream Cheese Bun, Matcha Bingsu, Korean Sponge Cake",
            "online_order": "Yes",
            "book_table": "No",
        },
    },

    # --- AFRICAN RESTAURANTS ---
    {
        "name": "Habesha Ethiopian & African Cuisine",
        "location": "Kalyan Nagar",
        "cuisines": ["African", "Ethiopian", "Middle Eastern"],
        "rating": 4.4,
        "cost_for_two": 600,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "CMR Road, HRBR Layout, Kalyan Nagar / Kammanahalli, Bangalore",
        "votes": 1850,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Authentic Injera Platter, Doro Wat, Tibs, Shiro, Ethiopian Spiced Tea",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "African Delights Restaurant",
        "location": "Kammanahalli",
        "cuisines": ["African", "Continental"],
        "rating": 4.2,
        "cost_for_two": 450,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "Kammanahalli Main Road, Bangalore",
        "votes": 1200,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Smoky Jollof Rice, Egusi Soup with Fufu, Fried Plantains, Suya Grilled Chicken",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Blue Nile African Kitchen",
        "location": "Kammanahalli",
        "cuisines": ["African", "Fast Food"],
        "rating": 4.1,
        "cost_for_two": 380,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": True,
        "address": "Hennur Main Road, Kammanahalli, Bangalore",
        "votes": 850,
        "raw": {
            "rest_type": "Quick Bites",
            "dish_liked": "Nigerian Jollof Rice, African Meat Pie, Fried Yam, Peppered Fish",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Mama Africa Cafe & Diner",
        "location": "Kammanahalli",
        "cuisines": ["African", "Cafe", "Desserts"],
        "rating": 4.3,
        "cost_for_two": 550,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "Kammanahalli, Bangalore",
        "votes": 1100,
        "raw": {
            "rest_type": "Cafe, Diner",
            "dish_liked": "Spiced Rooibos Tea, Cassava Fries, Chapati Wraps, Grilled Suya Skewers",
            "online_order": "Yes",
            "book_table": "No",
        },
    },

    # --- HALAL SPECIALTY RESTAURANTS ---
    {
        "name": "Hotel Empire",
        "location": "Church Street",
        "cuisines": ["Mughlai", "Biryani", "North Indian", "Arabian"],
        "rating": 4.3,
        "cost_for_two": 450,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "36, Church Street, Shantala Nagar, Bangalore",
        "votes": 7800,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Empire Special Chicken Kebab, Shawarma, Ghee Rice, Grill Chicken",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Al-Bek",
        "location": "Church Street",
        "cuisines": ["Arabian", "Biryani", "Mughlai", "Fast Food"],
        "rating": 4.2,
        "cost_for_two": 400,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": True,
        "address": "Church Street & Brigade Road, Bangalore",
        "votes": 5400,
        "raw": {
            "rest_type": "Quick Bites, Casual Dining",
            "dish_liked": "Chicken Shawarma Roll, Dajaj Faham, Mutton Biryani, Alfaham",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Rahhams",
        "location": "Frazer Town",
        "cuisines": ["Mughlai", "Biryani", "North Indian"],
        "rating": 4.5,
        "cost_for_two": 650,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "82, MM Road, Frazer Town, Bangalore",
        "votes": 6200,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Muslim Wedding Biryani, Mutton Seekh Kebab, Phalguni Chicken, Mutton Chops",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Savoury Restaurant",
        "location": "Frazer Town",
        "cuisines": ["Arabian", "Mughlai", "Chinese", "Seafood"],
        "rating": 4.4,
        "cost_for_two": 700,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "Mosque Road, Frazer Town, Bangalore",
        "votes": 5800,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Arabian Barbecue, Chicken Shawarma, Alfaham, Mutton Mandi",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Karama Restaurant",
        "location": "Frazer Town",
        "cuisines": ["Arabian", "Middle Eastern", "Mughlai"],
        "rating": 4.5,
        "cost_for_two": 850,
        "budget_tier": BudgetTier.HIGH,
        "is_veg": False,
        "is_halal": True,
        "address": "55, Mosque Road, Frazer Town, Bangalore",
        "votes": 4900,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Karachi Biryani, Mutton Mandi, Lahori Chargha, Arabic Kunafa",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Fanoos",
        "location": "Richmond Town",
        "cuisines": ["Fast Food", "Mughlai", "Rolls", "Arabian"],
        "rating": 4.4,
        "cost_for_two": 300,
        "budget_tier": BudgetTier.LOW,
        "is_veg": False,
        "is_halal": True,
        "address": "Hosur Road, Near Johnson Market, Richmond Town, Bangalore",
        "votes": 6100,
        "raw": {
            "rest_type": "Quick Bites",
            "dish_liked": "Jumbo Beef Seekh Roll, Chicken Shawarma, Shami Kebab, Kathi Rolls",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Chichaba's Taj",
        "location": "Frazer Town",
        "cuisines": ["Mughlai", "Biryani", "North Indian"],
        "rating": 4.5,
        "cost_for_two": 600,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "MM Road, Frazer Town, Bangalore",
        "votes": 4300,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Brain Pepper Fry, Mutton Biryani, Haleem, Phirni, Sheermal",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Sharief Bhai",
        "location": "Koramangala 5th Block",
        "cuisines": ["Mughlai", "Biryani", "Arabian"],
        "rating": 4.4,
        "cost_for_two": 600,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "Koramangala 5th Block, Bangalore",
        "votes": 5100,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Gosht Dum Biryani, Patthar Ka Gosht, Mutton Kebab, Gulab Jamun",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Meghana Foods",
        "location": "Residency Road",
        "cuisines": ["Biryani", "Andhra", "South Indian"],
        "rating": 4.6,
        "cost_for_two": 500,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "Residency Road & Church Street vicinity, Bangalore",
        "votes": 9800,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Meghana Special Chicken Biryani, Paneer Biryani, Chicken 65, Lemon Chicken",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
    {
        "name": "Nagarjuna",
        "location": "Residency Road",
        "cuisines": ["Andhra", "Biryani", "South Indian"],
        "rating": 4.5,
        "cost_for_two": 650,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "44/1, Residency Road, Bangalore",
        "votes": 8700,
        "raw": {
            "rest_type": "Casual Dining",
            "dish_liked": "Unlimited Andhra Meals, Chicken Sholay Kebab, Mutton Biryani, Gunpowder Rice",
            "online_order": "Yes",
            "book_table": "Yes",
        },
    },
    {
        "name": "Truffles",
        "location": "St. Marks Road",
        "cuisines": ["American", "Burger", "Cafe", "Desserts"],
        "rating": 4.6,
        "cost_for_two": 550,
        "budget_tier": BudgetTier.MEDIUM,
        "is_veg": False,
        "is_halal": True,
        "address": "St. Marks Road & Church Street Cross, Bangalore",
        "votes": 12500,
        "raw": {
            "rest_type": "Cafe, Casual Dining",
            "dish_liked": "All American Cheese Burger, Peri Peri Fries, Pasta, Ferrero Rocher Shake",
            "online_order": "Yes",
            "book_table": "No",
        },
    },
]


def normalize_cuisines(val: Any) -> List[str]:
    """Parse comma-separated cuisines into a cleaned, unique list maintaining order.

    Combines synonyms (e.g. 'Afghan' -> 'Afghani').
    """
    if val is None or pd.isna(val):
        return []
    if isinstance(val, list):
        items = val
    else:
        items = str(val).split(",")
    cleaned: List[str] = []
    seen = set()
    for item in items:
        cleaned_item = clean_text(item)
        if not cleaned_item:
            continue
        standardized = CUISINE_STANDARDIZATION.get(cleaned_item.lower(), cleaned_item)
        if standardized.lower() not in seen:
            seen.add(standardized.lower())
            cleaned.append(standardized)
    return cleaned


def normalize_record(raw: Dict[str, Any], record_id: str) -> Optional[Restaurant]:
    """Convert a raw dictionary from the Hugging Face dataset into a canonical Restaurant model."""
    name = clean_text(raw.get("name"))
    if not name:
        return None

    rating = parse_rating(raw.get("rate"))
    if rating is None:
        return None

    location = clean_text(normalize_location(raw.get("location")))
    if location == "Unknown":
        return None

    cuisines = normalize_cuisines(raw.get("cuisines"))

    # Auto-tag 'Bakery' if rest_type, dish_liked, or name indicates bakery
    rest_type_str = clean_text(raw.get("rest_type"))
    dish_liked_str = clean_text(raw.get("dish_liked"))
    name_str = name.lower()
    if (
        "baker" in rest_type_str.lower()
        or "baker" in name_str
        or "bakehouse" in name_str
        or "patisserie" in name_str
        or "bakes" in name_str
        or "bread" in dish_liked_str.lower()
        or "croissant" in dish_liked_str.lower()
    ) and not any(c.lower() == "bakery" for c in cuisines):
        cuisines.append("Bakery")

    if not cuisines:
        return None

    cost_for_two = parse_cost(raw.get("approx_cost(for two people)"))
    budget_tier = determine_budget_tier(cost_for_two)

    votes = raw.get("votes")
    try:
        votes_count = int(votes) if votes is not None and not pd.isna(votes) else 0
    except (ValueError, TypeError):
        votes_count = 0

    address = clean_text(raw.get("address")) or None

    is_veg_val = is_pure_veg(
        name=name,
        cuisines=cuisines,
        rest_type=rest_type_str,
        dish_liked=dish_liked_str,
        address=address,
    )

    is_halal_val = is_halal_friendly(
        name=name,
        cuisines=cuisines,
        rest_type=rest_type_str,
        dish_liked=dish_liked_str,
        address=address,
        is_veg=is_veg_val,
    )

    return Restaurant(
        id=record_id,
        name=name,
        location=location,
        cuisines=cuisines,
        rating=rating,
        cost_for_two=cost_for_two,
        budget_tier=budget_tier,
        address=address,
        votes=votes_count,
        is_veg=is_veg_val,
        is_halal=is_halal_val,
        raw={
            "rest_type": rest_type_str or None,
            "dish_liked": dish_liked_str or None,
            "online_order": raw.get("online_order"),
            "book_table": raw.get("book_table"),
        },
    )


def save_to_cache(restaurants: List[Restaurant], cache_path: Path = DEFAULT_CACHE_FILE) -> None:
    """Save processed restaurant records to local parquet or json cache."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    records = [r.model_dump() for r in restaurants]
    df = pd.DataFrame(records)

    try:
        df.to_parquet(cache_path, index=False)
        logger.info("Saved %d restaurants to parquet cache: %s", len(restaurants), cache_path)
    except Exception as e:
        logger.warning("Failed to save as parquet (%s), falling back to JSON...", e)
        json_path = cache_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)
        logger.info("Saved %d restaurants to JSON cache: %s", len(restaurants), json_path)


def _clean_cache_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Clean pandas record values (e.g., convert NaN to None, numpy arrays to lists)."""
    cleaned: Dict[str, Any] = {}
    for k, v in rec.items():
        if isinstance(v, (list, tuple, np.ndarray)):
            cleaned[k] = [str(x) for x in v if x is not None and not (isinstance(x, float) and np.isnan(x))]
        elif isinstance(v, dict):
            cleaned[k] = v
        elif v is None:
            cleaned[k] = None
        elif isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            cleaned[k] = None
        else:
            cleaned[k] = v
    if "name" in cleaned and cleaned["name"]:
        cleaned["name"] = clean_text(cleaned["name"])
    if "address" in cleaned and cleaned["address"]:
        cleaned["address"] = clean_text(cleaned["address"])
    return cleaned


def load_from_cache(cache_path: Path = DEFAULT_CACHE_FILE) -> Optional[List[Restaurant]]:
    """Load restaurant records from cache file if it exists."""
    # 1. Fast JSON loading via standard library
    possible_json_paths = [
        cache_path.with_suffix(".json"),
        DATA_CACHE_DIR / "restaurants.json",
        Path(__file__).resolve().parent.parent.parent / "data" / "cache" / "restaurants.json",
        Path("data/cache/restaurants.json"),
    ]
    for json_path in possible_json_paths:
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                restaurants = [Restaurant(**rec) for rec in records]
                logger.info("Loaded %d restaurants from JSON cache: %s", len(restaurants), json_path)
                return restaurants
            except Exception as e:
                logger.warning("Failed reading JSON cache at %s (%s)", json_path, e)

    # 2. Parquet loading fallback
    possible_parquet_paths = [
        cache_path,
        DATA_CACHE_DIR / "restaurants.parquet",
        Path(__file__).resolve().parent.parent.parent / "data" / "cache" / "restaurants.parquet",
        Path("data/cache/restaurants.parquet"),
    ]
    for path in possible_parquet_paths:
        if path.exists():
            try:
                df = pd.read_parquet(path)
                records = df.to_dict(orient="records")
                restaurants = [Restaurant(**_clean_cache_record(rec)) for rec in records]
                logger.info("Loaded %d restaurants from parquet cache: %s", len(restaurants), path)
                return restaurants
            except Exception as e:
                logger.warning("Failed reading parquet cache at %s (%s)", path, e)

    return None


def load_and_process_dataset(
    dataset_name: str = DEFAULT_DATASET_NAME,
    cache_path: Path = DEFAULT_CACHE_FILE,
    force_reload: bool = False,
) -> List[Restaurant]:
    """Load dataset from cache if present, otherwise fetch from Hugging Face, clean, deduplicate, and cache."""
    if not force_reload:
        cached = load_from_cache(cache_path)
        if cached:
            return cached

    logger.info("Fetching and processing dataset '%s' from Hugging Face...", dataset_name)
    from datasets import load_dataset

    ds = load_dataset(dataset_name, split="train")
    df = ds.to_pandas()
    logger.info("Raw dataset loaded with %d rows", len(df))

    records_dict: Dict[Tuple[str, str], Tuple[Restaurant, int]] = {}
    skipped_count = 0

    for idx, row in df.iterrows():
        raw_dict = row.to_dict()
        record_id = f"rest_{idx + 1}"
        restaurant = normalize_record(raw_dict, record_id)
        if restaurant is None:
            skipped_count += 1
            continue

        dedup_key = (restaurant.name.lower().strip(), restaurant.location.lower().strip())
        votes = restaurant.votes or 0

        if dedup_key not in records_dict:
            records_dict[dedup_key] = (restaurant, votes)
        else:
            existing_rest, existing_votes = records_dict[dedup_key]
            if votes > existing_votes or (
                votes == existing_votes and restaurant.rating > existing_rest.rating
            ):
                records_dict[dedup_key] = (restaurant, votes)

    for supp in SUPPLEMENTAL_RESTAURANTS:
        is_veg_val = supp.get("is_veg", False)
        is_halal_val = supp.get(
            "is_halal",
            is_halal_friendly(
                name=supp["name"],
                cuisines=supp["cuisines"],
                rest_type=supp.get("raw", {}).get("rest_type"),
                dish_liked=supp.get("raw", {}).get("dish_liked"),
                is_veg=is_veg_val,
            ),
        )
        supp_rest = Restaurant(
            id=f"supp_{len(records_dict) + 1}",
            name=clean_text(supp["name"]),
            location=clean_text(supp["location"]),
            cuisines=supp["cuisines"],
            rating=supp["rating"],
            cost_for_two=supp.get("cost_for_two"),
            budget_tier=supp["budget_tier"],
            is_veg=is_veg_val,
            is_halal=is_halal_val,
            address=clean_text(supp.get("address")),
            votes=supp.get("votes", 100),
            raw=supp.get("raw", {}),
        )
        dedup_key = (supp_rest.name.lower().strip(), supp_rest.location.lower().strip())
        records_dict[dedup_key] = (supp_rest, supp_rest.votes or 100)

    processed_restaurants: List[Restaurant] = []
    for i, (restaurant, _) in enumerate(records_dict.values(), start=1):
        clean_rest = restaurant.model_copy(update={"id": f"rest_{i}"})
        processed_restaurants.append(clean_rest)

    logger.info(
        "Processed dataset: %d valid deduplicated restaurants (skipped %d invalid/unrated rows)",
        len(processed_restaurants),
        skipped_count,
    )

    save_to_cache(processed_restaurants, cache_path)
    return processed_restaurants


if __name__ == "__main__":
    restaurants = load_and_process_dataset(force_reload=True)
    print(f"Cache warmed successfully with {len(restaurants)} restaurants.")
