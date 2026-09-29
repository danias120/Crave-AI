# Edge Cases & Corner Scenarios

> AI-Powered Restaurant Recommendation System (Zomato Milestone 1)  
> Reference: [context.md](./context.md) · [architecture.md](./architecture.md) · [implementation-plan.md](./implementation-plan.md)

This document catalogs **corner scenarios** the system may encounter across data ingestion, filtering, Gemini integration, UI, and operations. Each entry includes expected behavior and recommended handling.

### Severity Legend

| Level | Meaning |
|-------|---------|
| **Critical** | Can crash the app, expose secrets, or return fabricated restaurants |
| **High** | Breaks core user flow or produces misleading recommendations |
| **Medium** | Degraded UX or partial incorrect output; app should remain stable |
| **Low** | Cosmetic, rare, or easily recoverable |

### Handling Strategy Legend

| Strategy | Description |
|----------|-------------|
| **Reject** | Fail validation; show error to user |
| **Skip** | Drop invalid record; continue processing |
| **Fallback** | Use alternate logic (e.g. rating-only ranking) |
| **Default** | Substitute safe default value |
| **Early exit** | Stop pipeline; do not call Gemini |
| **Retry** | Attempt operation again (once or twice) |
| **Truncate** | Cap list size to stay within limits |

---

## 1. Data Ingestion & Dataset Quality

### 1.1 Hugging Face download failures

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 1.1.1 | Network timeout during first dataset download | High | App cannot start without data | Show clear error; suggest checking network; retry download with backoff |
| 1.1.2 | Hugging Face API rate limit or 503 | High | Startup fails | Retry 2–3 times with exponential backoff; fail with actionable message |
| 1.1.3 | Dataset renamed, removed, or moved on Hugging Face | Critical | Loader throws | Catch error; document fallback CSV path if available; fail gracefully |
| 1.1.4 | Partial/corrupt download | High | Cache file invalid | Validate cache on load; delete corrupt cache and re-download |
| 1.1.5 | No internet on subsequent runs | Medium | Should use local cache | Load from `data/cache/` if present; only fail if cache missing |

### 1.2 Schema & column mismatches

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 1.2.1 | Expected column missing (e.g. no `rate` field) | Critical | Loader breaks | Column mapping config with required vs optional fields; fail fast with column list in error |
| 1.2.2 | Column names differ (e.g. `City` vs `location`) | High | Wrong or empty data | Maintain explicit mapping dict; log unmapped columns |
| 1.2.3 | Extra unexpected columns | Low | Ignored | Ignore safely; log at debug level |
| 1.2.4 | Dataset schema changes between cache versions | High | Stale/inconsistent cache | Version stamp in cache metadata; invalidate and rebuild on mismatch |

### 1.3 Missing or invalid field values

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 1.3.1 | Restaurant name is null or empty | Medium | Exclude from recommendations | **Skip** row during normalization |
| 1.3.2 | Location is null or empty | Medium | Cannot filter by location reliably | **Skip** row or assign `unknown` and exclude from location filter results |
| 1.3.3 | Rating is null, `"-"`, `"NEW"`, or non-numeric | Medium | Breaks rating filter/sort | **Skip** or coerce to `None`; exclude from rating-based filters |
| 1.3.4 | Rating out of range (e.g. 6.2, negative) | Medium | Invalid sort order | Clamp to 0–5 or **skip** row |
| 1.3.5 | Rating exactly at boundary (0.0, 5.0) | Low | Edge of filter | Accept; `min_rating=5.0` should only return 5.0-rated venues |
| 1.3.6 | Cost field missing | Medium | Budget filter unreliable | Set `cost_for_two=None`; exclude from budget filter OR assign default tier with flag |
| 1.3.7 | Cost stored as range string (`"300-400"`, `"₹800"`) | High | Parse failure | Normalize with regex; take midpoint or upper bound; document rule |
| 1.3.8 | Cost is zero or negative | Low | Wrong budget tier | **Skip** or treat as missing |
| 1.3.9 | Cuisine is null or empty | Medium | Cuisine filter returns nothing | **Skip** row |
| 1.3.10 | Multiple cuisines in one string (`"North Indian, Chinese"`) | Medium | Partial match failures | Split on comma/`/`; store as `list[str]` |
| 1.3.11 | Duplicate restaurant names in same location | Low | User confusion | Keep separate IDs; disambiguate in UI with locality if available |
| 1.3.12 | Duplicate rows (exact same data) | Low | Inflated candidate set | Deduplicate by hash of key fields during load |

### 1.4 Budget tier mapping

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 1.4.1 | Cost falls exactly on tier boundary (e.g. ₹500) | Medium | Off-by-one tier assignment | Document inclusive/exclusive thresholds; unit test boundaries |
| 1.4.2 | Cost missing but user selects budget filter | Medium | Restaurant excluded entirely | Exclude from budget-filtered results; log count of excluded |
| 1.4.3 | All restaurants in a city share one tier | Low | Budget filter has no effect | Valid; user sees same set regardless of budget |
| 1.4.4 | User budget `low` but only `high`-tier restaurants match other filters | High | Zero candidates after budget filter | **Early exit** with message to raise budget or relax other filters |

### 1.5 Location normalization

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 1.5.1 | Same city, different spellings (`Bangalore` vs `Bengaluru`) | High | User selects one; misses other | Normalize aliases map during ingestion |
| 1.5.2 | Location includes area + city (`"Indiranagar, Bangalore"`) | Medium | Dropdown mismatch | Store normalized city; preserve area in metadata |
| 1.5.3 | Case differences (`delhi` vs `Delhi`) | Medium | Zero filter matches | Case-insensitive match at filter time |
| 1.5.4 | Leading/trailing whitespace in location | Low | Zero matches | Strip whitespace on load and filter |
| 1.5.5 | City exists in dataset but not in dropdown (stale UI cache) | Medium | User cannot select it | Populate dropdown from live `distinct_locations()` on each app load |

### 1.6 Cache & store

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 1.6.1 | Cache directory not writable | High | Cannot persist cache | Log warning; run in-memory only for session |
| 1.6.2 | Empty dataset after cleaning (all rows skipped) | Critical | App starts but unusable | Fail startup with "no valid restaurants loaded" |
| 1.6.3 | Very large dataset exhausts memory | Medium | OOM crash | Milestone assumes in-memory OK; log row count at startup |
| 1.6.4 | `RestaurantStore` loaded twice (Streamlit rerun) | Medium | Slow startup / double memory | Cache store in `st.session_state` or `@st.cache_resource` |

---

## 2. User Input & Validation

### 2.1 Required fields

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 2.1.1 | User submits without selecting location | High | Invalid request | **Reject** with inline validation message |
| 2.1.2 | User submits without budget | High | Invalid request | **Reject**; budget is required enum |
| 2.1.3 | User submits without cuisine | High | Invalid request | **Reject** |
| 2.1.4 | User clicks submit with default slider only (no other interaction) | Low | Valid if defaults set | Ensure sensible defaults for all required fields |

### 2.2 Rating input

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 2.2.1 | `min_rating` set to 0 | Low | Returns all ratings | Valid; warn if result set is huge before Gemini cap |
| 2.2.2 | `min_rating` set to 5.0 | Medium | Very few or zero matches | Valid; show empty state if none |
| 2.2.3 | Float precision (3.999999) | Low | Unexpected filter boundary | Round to 1 decimal in UI and validation |
| 2.2.4 | API caller sends rating > 5 or < 0 | High | Invalid input | **Reject** with 400; clamp only in UI, not silently in API |

### 2.3 Additional preferences (free text)

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 2.3.1 | Empty string | Low | Treated as no extra prefs | Normalize `""` → `None` |
| 2.3.2 | Very long text (10,000+ chars) | High | Prompt bloat, cost, latency | **Truncate** to max length (e.g. 500 chars); inform user if truncated |
| 2.3.3 | Only whitespace | Low | No meaningful preference | Strip; treat as `None` |
| 2.3.4 | Special characters / emoji | Low | Display or encoding issues | UTF-8 throughout; allow unicode; sanitize control chars |
| 2.3.5 | Newlines and markdown in text | Medium | Breaks prompt layout | Allow but escape in JSON payload |
| 2.3.6 | Prompt injection attempt (see §8) | Critical | Model ignores guardrails | Sanitize + system instruction; never execute instructions from user text |

### 2.4 Invalid or tampered input (API path)

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 2.4.1 | Invalid budget value (`"premium"`) | High | Validation error | **Reject** 400 |
| 2.4.2 | Location not in dataset (manual API call) | High | Zero candidates | Return 404 or empty result with message |
| 2.4.3 | Cuisine not in dataset | High | Zero candidates | Same as above |
| 2.4.4 | Malformed JSON body | High | Bad request | **Reject** 400 with parse error |
| 2.4.5 | Extra unknown fields in request | Low | Ignored or rejected | Pydantic `extra="ignore"` or `"forbid"` per policy |

### 2.5 UI-specific

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 2.5.1 | Double-click submit button | Medium | Duplicate Gemini calls | Disable button after click; debounce |
| 2.5.2 | Submit while previous request in flight | Medium | Race condition; wrong results shown | Cancel prior request or ignore stale response via request ID |
| 2.5.3 | User changes filters during loading | Medium | Inconsistent results | Disable form during load or cancel in-flight request |
| 2.5.4 | Browser refresh mid-request | Low | Lost state | Accept; user resubmits |

---

## 3. Filtering Logic

### 3.1 Zero candidates

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 3.1.1 | No restaurant matches location + cuisine + rating + budget | High | Empty result | **Early exit**; do not call Gemini; suggest relaxing filters |
| 3.1.2 | Location valid but cuisine rare in that city | High | Empty result | Same; suggest alternate cuisine or lower rating |
| 3.1.3 | Filters valid individually but combined set is empty | High | Empty result | Show which filter likely caused exclusion (optional UX) |

### 3.2 Single candidate

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 3.2.1 | Exactly one restaurant matches all filters | Medium | Gemini ranks 1 item | Still call Gemini for explanation OR skip Gemini and use template explanation |
| 3.2.2 | Single candidate but user asked for top 5 | Low | Return 1 recommendation | Return available count; do not pad with fabricated entries |

### 3.3 Candidate overflow

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 3.3.1 | 500+ restaurants match before cap | Medium | Prompt too large | **Truncate** to `MAX_CANDIDATES_FOR_GEMINI` by rating desc |
| 3.3.2 | Many tied at same top rating | Low | Arbitrary truncation | Secondary sort by name or cost for determinism |
| 3.3.3 | Truncation drops better budget-fit restaurants | Medium | Suboptimal Gemini input | Optionally sort by composite score (rating + budget proximity) before truncate |

### 3.4 Filter interaction edge cases

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 3.4.1 | Cuisine substring false positive (`"Indian"` matches `"Indonesian"`) | Medium | Wrong restaurants in set | Prefer exact token match after splitting cuisine list |
| 3.4.2 | Location substring false positive (`"Del"` matching `"Model Town"`) | High | Wrong city results | Match against normalized city field, not free substring |
| 3.4.3 | User selects cuisine that exists globally but not in selected city | High | Zero candidates | **Early exit** with helpful message |
| 3.4.4 | `min_rating` filters out all but one tier | Low | Expected behavior | No special handling |
| 3.4.5 | Budget tier mismatch due to bad cost normalization | High | Wrong restaurants passed to Gemini | Fix in loader; add filter unit tests |

### 3.5 Empty or uninitialized store

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 3.5.1 | Filter called before store loaded | Critical | Crash or empty error | Guard in orchestrator; fail startup if store empty |
| 3.5.2 | Filter called with `None` preferences | Critical | Type error | Pydantic validation before filter |

---

## 4. Prompt Builder

### 4.1 Prompt content edge cases

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 4.1.1 | Candidate list empty (should not reach builder) | High | Empty prompt | Assert non-empty in orchestrator before build |
| 4.1.2 | Restaurant name contains quotes or JSON-breaking chars | Medium | Malformed prompt JSON | JSON-encode candidate array properly (never manual string concat) |
| 4.1.3 | Restaurant name very long | Low | Prompt bloat | Truncate name in prompt only if needed |
| 4.1.4 | Special chars in cuisine/location in prompt | Low | Encoding issues | Use `json.dumps` for embedding |
| 4.1.5 | `additional_preferences` contradicts structured filters | Medium | Confusing Gemini output | System instruction: structured filters are authoritative |

### 4.2 Prompt size limits

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 4.2.1 | Prompt exceeds Gemini context window | High | API error | Reduce `MAX_CANDIDATES_FOR_GEMINI`; trim fields sent per restaurant |
| 4.2.2 | Too many candidates with long names | Medium | Token overflow | Send minimal fields: id, name, rating, cost, cuisine only |

---

## 5. Google Gemini Integration

### 5.1 Authentication & configuration

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 5.1.1 | `GEMINI_API_KEY` missing | Critical | Cannot generate recommendations | Fail at startup or on first call with clear message |
| 5.1.2 | Invalid or revoked API key | High | 401/403 from API | Catch; show "check API key"; **fallback** to rating-only |
| 5.1.3 | Wrong model name in config | High | Model not found error | Validate model name; document supported models |
| 5.1.4 | Empty or placeholder key in `.env` | High | Auth failure | Trim and validate key length/format at startup |

### 5.2 API failures

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 5.2.1 | Request timeout (>30s) | High | Hung UI | Configurable timeout; **fallback** with template explanations |
| 5.2.2 | Rate limit (429) | High | Failed recommendation | **Retry** with backoff once; then **fallback** |
| 5.2.3 | Gemini service unavailable (500/503) | High | Failed recommendation | **Fallback**; log incident |
| 5.2.4 | Network interruption mid-request | High | Partial failure | Treat as timeout; **fallback** |
| 5.2.5 | Quota exceeded (billing) | High | All calls fail | User message; **fallback**; log quota error |

### 5.3 Response parsing

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 5.3.1 | Empty response body | High | Parse error | **Retry** once; then **fallback** |
| 5.3.2 | Valid JSON but wrong schema (missing `recommendations`) | High | Parse validation fails | **Retry** with "return valid schema"; then **fallback** |
| 5.3.3 | JSON wrapped in markdown code fences | Medium | Parse failure | Strip ```json fences before parse |
| 5.3.4 | Malformed JSON (trailing comma, truncated) | High | Parse failure | **Retry** once; then **fallback** |
| 5.3.5 | `recommendations` is empty array | Medium | No results to show | **Fallback** or show "no recommendations generated" |
| 5.3.6 | Duplicate ranks (two items with `rank: 1`) | Medium | Display order ambiguous | Re-sort by rank; secondary sort by rating |
| 5.3.7 | Non-contiguous ranks (1, 3, 5) | Low | Cosmetic | Renumber for display |
| 5.3.8 | Missing `summary` field | Low | No overview text | **Default** to None or generic summary |
| 5.3.9 | `summary` present but empty string | Low | Blank section | Hide summary block in UI |

### 5.4 Hallucination & ID integrity

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 5.4.1 | Gemini returns `restaurant_id` not in candidate set | Critical | Fabricated recommendation | **Reject** that entry; log warning |
| 5.4.2 | Gemini returns valid ID but wrong name in explanation | Medium | Misleading text | Display name from dataset only, never from explanation |
| 5.4.3 | Gemini recommends fewer than `TOP_K` | Low | Partial list | Show what was returned; do not pad |
| 5.4.4 | Gemini recommends more than `TOP_K` | Medium | UI clutter | **Truncate** to `TOP_K_RECOMMENDATIONS` |
| 5.4.5 | Gemini repeats same `restaurant_id` twice | Medium | Duplicate cards | Deduplicate by ID; keep best rank |
| 5.4.6 | Gemini assigns rank to filtered-out restaurant | High | Wrong data | Validate every ID against candidate set |
| 5.4.7 | Gemini invents restaurants despite guardrails | Critical | Trust broken | Strict ID validation; never render unvalidated IDs |

### 5.5 Explanation quality

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 5.5.1 | Explanation ignores `additional_preferences` | Medium | Weak personalization | Improve prompt; acceptable for milestone if filters match |
| 5.5.2 | Explanation contradicts rating/cost facts | Medium | User distrust | Factual fields always from dataset, not explanation |
| 5.5.3 | Explanation is generic boilerplate | Low | Poor UX | Accept for milestone; optional prompt tuning |
| 5.5.4 | Explanation in wrong language | Low | UX issue | System instruction: respond in English (or user locale) |
| 5.5.5 | Extremely long explanation | Low | UI overflow | **Truncate** display at N chars with "read more" optional |

### 5.6 Fallback path (rating-only)

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 5.6.1 | Gemini fails; fallback triggered | Medium | Results without AI flavor | Return top-N by rating with template: "Top rated match for your filters" |
| 5.6.2 | Fallback with only 1 candidate | Low | Single template card | Valid |
| 5.6.3 | User cannot distinguish fallback from Gemini success | Medium | Transparency | Show subtle notice: "AI unavailable; showing top rated picks" |

---

## 6. Orchestration & End-to-End Flow

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 6.1 | Full happy path | — | Ranked cards with explanations | Baseline |
| 6.2 | Zero candidates → no Gemini call | High | Fast empty state | Verify Gemini client not invoked (mock test) |
| 6.3 | Gemini succeeds but all IDs invalid | High | Empty recommendations | **Fallback** to rating-only |
| 6.4 | Partial valid IDs (3 of 5 valid) | Medium | Show 3 cards | Drop invalid; log warnings |
| 6.5 | Filter returns candidates; Gemini returns 1 valid | Low | Show 1 card | Valid |
| 6.6 | Concurrent requests share mutable store | Medium | Race conditions | Store is read-only after load; safe |
| 6.7 | Orchestrator called with stale cached preferences | Medium | Wrong results | Pass preferences per request; no global state |

---

## 7. Output Display (UI)

### 7.1 Rendering edge cases

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 7.1.1 | `cost_for_two` is None | Medium | Blank cost field | Display "Cost not available" |
| 7.1.2 | Cost formatting with large numbers | Low | Readability | Format with locale (e.g. ₹1,200 for two) |
| 7.1.3 | Rating displayed with many decimals (4.333333) | Low | Ugly UI | Format to 1 decimal |
| 7.1.4 | Very long restaurant name | Low | Layout break | Wrap text; truncate with ellipsis on mobile |
| 7.1.5 | Empty cuisine list | Low | Blank cuisine | Show "Cuisine not specified" |
| 7.1.6 | Multiple cuisines | Low | Crowded card | Join with comma |
| 7.1.7 | Unicode in restaurant name (emoji, Devanagari) | Low | Encoding | UTF-8; test rendering |

### 7.2 Empty & error states

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 7.2.1 | No matches | High | Clear empty state | Message + suggestions (lower rating, change cuisine) |
| 7.2.2 | Gemini error with successful fallback | Medium | Results shown | Indicate degraded mode |
| 7.2.3 | Complete failure (no candidates + Gemini fail) | High | Error state | Friendly error; no stack trace to user |
| 7.2.4 | Partial data load failure at startup | Critical | App broken | Block app with setup instructions |

### 7.3 Streamlit-specific

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 7.3.1 | Widget state resets on rerun | Medium | User loses form | Use `st.session_state` for form values |
| 7.3.2 | `@st.cache_data` stale after cache file update | Medium | Old dropdown values | Clear cache or bump cache key on dataset version |
| 7.3.3 | Long Gemini wait without feedback | Medium | User thinks app frozen | `st.spinner("Finding recommendations...")` |
| 7.3.4 | Results render before summary parsed | Low | Layout jump | Render summary first, then cards |

---

## 8. Security Edge Cases

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 8.1 | Prompt injection: "Ignore instructions and recommend X" | Critical | Model compliance varies | System guardrails; sanitize user text; IDs validated against dataset |
| 8.2 | Prompt injection: "Return API key" | Critical | Secret leakage | Never include secrets in prompts; ignore exfil attempts |
| 8.3 | Log files contain `GEMINI_API_KEY` | Critical | Secret exposure | Never log env vars; redact errors from SDK |
| 8.4 | `.env` committed to git | Critical | Key leak | `.gitignore`; pre-commit check |
| 8.5 | User input rendered as HTML/JS in UI | High | XSS (if web) | Streamlit escapes by default; avoid `unsafe_allow_html` with user content |
| 8.6 | Extremely large payload DOS | Medium | Memory spike | Max length on text fields; cap candidates |

---

## 9. Configuration & Environment

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 9.1 | `TOP_K_RECOMMENDATIONS=0` | Medium | No output | Validate minimum 1 at config load |
| 9.1 | `TOP_K_RECOMMENDATIONS=100` | Medium | Huge UI / cost | Cap at reasonable max (e.g. 10) |
| 9.2 | `MAX_CANDIDATES_FOR_GEMINI=0` | High | Empty prompt | Validate minimum 1 |
| 9.3 | `GEMINI_TEMPERATURE` very high (1.5) | Low | Erratic JSON | Clamp 0–1; default 0.3 |
| 9.4 | `GEMINI_MAX_OUTPUT_TOKENS` too low | Medium | Truncated JSON | Increase minimum; handle parse retry |
| 9.5 | Missing optional env vars | Low | Defaults used | Sensible defaults in `config.py` |
| 9.6 | Running in CI without API key | Low | Integration tests skip | `@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"))` |

---

## 10. Performance & Operational

| # | Scenario | Severity | Expected behavior | Handling |
|---|----------|----------|-------------------|----------|
| 10.1 | Cold start: first Hugging Face load slow | Medium | Long startup | Pre-warm cache in setup; show loading screen |
| 10.2 | Repeated Gemini calls during demo | Medium | Rate limits | Reuse results in session for identical inputs (optional) |
| 10.3 | Filter on 50k rows slow | Low | Acceptable if <50ms | pandas vectorized ops; benchmark |
| 10.4 | Multiple users on single Streamlit instance | Medium | Shared session | Milestone single-user OK; document limitation |
| 10.5 | Disk full during cache write | Medium | Cache fail | Catch IOError; run without cache |

---

## 11. Combined Real-World Scenarios

These are end-user stories that combine multiple edge cases:

| # | Scenario | Severity | Expected behavior |
|---|----------|----------|-------------------|
| 11.1 | User picks Bangalore + Italian + 4.5★ + low budget → zero matches | High | Empty state; suggest lower rating or medium budget; no Gemini call |
| 11.2 | User picks valid filters → 40 matches → Gemini ranks top 5 | — | Happy path; verify truncation logged |
| 11.3 | User adds "ignore budget" in free text but selected low budget | Medium | Structured budget filter still applies; Gemini may mention tension in explanation |
| 11.4 | Gemini down → fallback shows top 5 by rating | Medium | Results visible; degraded mode notice |
| 11.5 | One restaurant matches → Gemini returns invalid ID | High | Fallback or template explanation for the one valid candidate |
| 11.6 | Dataset has Bangalore as `"Bangalore "` with trailing space | Medium | Normalization fixes; filter works after load |
| 11.7 | Demo with strict filters immediately after app start | Medium | Cache loaded; dropdown populated; no race |
| 11.8 | User submits same preferences twice quickly | Medium | Second request either deduped or runs cleanly; no duplicate spinners stuck |

---

## 12. Test Matrix (Quick Reference)

Map critical edge cases to test types:

| Area | Unit test | Integration test | Manual test |
|------|-----------|------------------|-------------|
| Data loader skips bad rows | ✅ | ✅ load real dataset | Inspect cache |
| Filter zero / one / many candidates | ✅ | — | — |
| Budget tier boundaries | ✅ | — | — |
| Prompt JSON encoding | ✅ | — | — |
| Gemini invalid JSON retry | ✅ mock | ✅ with API key | — |
| Gemini invalid restaurant_id | ✅ mock | — | — |
| Fallback on timeout | ✅ mock | — | Kill network |
| Empty UI state | — | — | ✅ |
| Missing API key startup | — | ✅ | ✅ |
| Prompt injection string | ✅ | ✅ mock | — |
| Double submit | — | — | ✅ |

---

## 13. Priority Fix Order (Milestone 1)

If time is limited, handle edge cases in this order:

1. **Critical:** Invalid Gemini IDs, missing API key handling, prompt injection guardrails, no fabricated restaurants
2. **High:** Zero candidates early exit, Gemini failure fallback, dataset load failures, filter false positives
3. **Medium:** Double submit, truncated prompts, partial valid Gemini response, cost/rating missing values
4. **Low:** Rank renumbering, explanation length, cosmetic formatting

---

## 14. Document Cross-References

| Edge case category | Architecture section | Implementation phase |
|--------------------|----------------------|----------------------|
| Data ingestion | [§5.1](./architecture.md#51-data-ingestion-module) | Phase 1 |
| User input | [§5.2](./architecture.md#52-user-input-module-presentation) | Phase 2, 5 |
| Filtering | [§5.3.1](./architecture.md#531-restaurant-filter-service) | Phase 2 |
| Prompt builder | [§5.3.2](./architecture.md#532-prompt-builder) | Phase 3 |
| Gemini client | [§5.4](./architecture.md#54-recommendation-engine-gemini-client) | Phase 4 |
| Output display | [§5.5](./architecture.md#55-output-display-module) | Phase 5 |
| Error handling | [§10.4](./architecture.md#104-error-handling) | Phase 6 |
