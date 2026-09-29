# 🍽️ Crave AI — Intelligent Food Discovery & Recommendation Engine

> **Crave AI** is an AI-powered culinary discovery engine built on real-world Bangalore restaurant dataset (9,250+ spots). Driven by **Google Gemini 2.5 Flash** and a multi-stage deterministic pre-filtering pipeline, Crave AI transforms vague cravings, strict dietary rules, and group conflicts into personalized, high-confidence dining recommendations.

---

## ✨ Features

### 1. 🔍 Discover (Main AI Food Discovery)
* **Natural Language Preferences**: Express complex desires like *"cozy candle-lit rooftop with outdoor seating"* or *"halal-friendly authentic mutton biryani"*.
* **Deterministic Stage-1 Filtering**: Hard constraints on location, budget tiers (Low `<₹500`, Medium `₹500–1500`, High `₹1500+`), and pure vegetarian status are filtered before LLM synthesis.
* **LLM Stage-2 Ranking & Synthesis**: Google Gemini evaluates top candidate menus, reviews, and ambiance to produce ranked recommendations with AI-crafted explanations.
* **Vegetarian & Halal Filtering**: Dedicated pure veg toggle and automated halal-friendly restaurant classification.

### 2. 🍜 Dish Radar
* **Hyper-Specific Craving Scanner**: Search for exact dishes rather than generic cuisine labels (*e.g., Tonkotsu Ramen, Yemeni Mandi, Butter Masala Dosa, Basque Cheesecake, Mutton Shawarma, Korean Bingsu*).
* **Dish Radar Intel**: Highlights menu matches and foodie review excerpts for why that spot excels at that specific dish.

### 3. 🎲 Crave Roulette
* **Surprise Me Spin Engine**: Solves decision paralysis with a weighted randomized selection algorithm.
* **Winning Reveal**: Includes **Must-Order Dish**, **Why It Won Tonight**, and **Insider Pro Foodie Tip**.

### 4. 👥 Group Dining Solver
* **Conflict Resolution**: Solves conflicting group dietary requirements (e.g., pure vegetarian, vegan, halal-only, gluten-free, omnivore).
* **Harmony Scoring**: Calculates a 0–100% group harmony score and provides individual meal plans for each person.

---

## 🏗️ Architecture

```
User Request
    │
    ▼
FastAPI Backend (/api/recommendations, /api/dish-search, /api/roulette, /api/group-recommendations)
    │
    ├─► Stage 1: Deterministic Filter (pandas / in-memory RestaurantStore)
    │     ├── Location matching (case-insensitive)
    │     ├── Budget Tier categorization
    │     ├── Pure Veg / Halal classification
    │     ├── Rating threshold & vote volume filtering
    │     └── Top Candidate Selection (up to 15 candidates)
    │
    ├─► Stage 2: Gemini 2.5 Flash LLM Reasoner
    │     ├── Structured Prompt with user intent & candidates
    │     └── JSON-schema constrained response (rankings & explanations)
    │
    └─► Vite + React Frontend
          ├── Design System (Zomato-inspired dark theme, Outfit + Inter typography)
          ├── Real-time search & debounced autocomplete
          └── Responsive UI with micro-animations & fallback states
```

---

## 🚀 Quick Start

### Prerequisites
* Python 3.9+
* Node.js 18+ and npm
* Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

---

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/danias120/Zomato-Milstone1.git
cd Zomato-Milstone1

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
```

Run the backend server:
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing

Run backend test suite (47 unit and integration tests):
```bash
.venv/bin/pytest
```

Run frontend build check:
```bash
cd frontend && npm run build
```

---

## 📁 Project Structure

```
.
├── src/
│   ├── api/                  # FastAPI routers and endpoints
│   ├── data/                 # In-memory store and dataset processing
│   ├── models/               # Pydantic data schemas
│   └── services/             # Filtering, Gemini LLM, and feature services
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios HTTP client
│   │   ├── components/       # UI views and components
│   │   ├── styles/           # Design system tokens and globals
│   │   └── types/            # TypeScript interfaces
├── tests/                    # Pytest test suite
├── docs/                     # Architecture and specification documentation
├── requirements.txt
└── .gitignore
```

---

## 📄 License
MIT License.
