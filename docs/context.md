# Project Context: AI-Powered Restaurant Recommendation System

> Source: [problem-statement.txt](./problem-statement.txt)

## Overview

Build an **AI-powered restaurant recommendation service** inspired by Zomato. The system intelligently suggests restaurants based on user preferences by combining **structured restaurant data** with a **Large Language Model (LLM)**.

## Objective

Design and implement an application that:

- Takes user preferences (location, budget, cuisine, ratings, and more)
- Uses a real-world dataset of restaurants
- Leverages an LLM to generate personalized, human-like recommendations
- Displays clear and useful results to the user

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:
  - **Dataset URL:** https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation
- Extract relevant fields, including:
  - Restaurant name
  - Location
  - Cuisine
  - Cost
  - Rating
  - Other applicable metadata from the dataset

### 2. User Input

Collect user preferences:

| Preference | Examples |
|------------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | Low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional preferences** | Family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare relevant restaurant data based on user input
- Pass structured results into an LLM prompt
- Design a prompt that helps the LLM reason over and rank options

### 4. Recommendation Engine

Use the LLM to:

- Rank restaurants
- Provide explanations (why each recommendation fits the user's preferences)
- Optionally summarize the overall set of choices

### 5. Output Display

Present top recommendations in a user-friendly format. Each recommendation should include:

- **Restaurant name**
- **Cuisine**
- **Rating**
- **Estimated cost**
- **AI-generated explanation** (why this restaurant was recommended)

## Data Source

| Field | Value |
|-------|-------|
| Platform | Hugging Face |
| Dataset | `ManikaSaini/zomato-restaurant-recommendation` |
| Link | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |

## Key Requirements Summary

1. **Structured filtering** — Narrow the dataset using explicit user criteria before LLM processing.
2. **LLM integration** — Use the model for ranking, reasoning, and natural-language explanations—not as the sole source of restaurant data.
3. **Personalization** — Recommendations must reflect the user's stated location, budget, cuisine, rating floor, and optional preferences.
4. **Clear UX** — Output must be readable and actionable, with both factual fields and AI-generated rationale.

## Expected End-to-End Flow

```
User preferences → Filter dataset → Build LLM prompt → LLM ranks & explains → Display top picks
```

## Out of Scope (Not Specified in Problem Statement)

The problem statement does not define:

- Specific tech stack (frontend, backend, language, framework)
- LLM provider or model choice
- Deployment target
- Authentication or user accounts
- Number of recommendations to return

These decisions are left to the implementation phase.
