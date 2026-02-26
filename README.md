# Scentscape — Perfume Explorer

A curated fragrance discovery app with data scraped from Fragrantica. Browse, filter, and explore 898 perfumes from 60+ designer and niche houses with rich metadata: notes, longevity, sillage, price value, seasonality, and main accords.

---

## Features

### Explore
- **Search** by perfume name or house
- **Filter** by house, category (designer/niche/luxury), gender, accord, note
- **Chip filters** for season (🌸☀️🍂❄️), longevity, sillage, and price value
- **Sort** by rating, votes, name, or release year
- Paginated grid with smooth animations

### Perfume Cards
- Local perfume images (900+ photos)
- Accord-based **glow effects** on hover — each accord family has its own color
- Star rating, vote count, and top note tags

### Perfume Modal
- Full note pyramid (top / heart / base notes)
- Main accords with accent coloring
- **Vote metrics as icons:**
  - **Longevity** — 5 fill bars (Very Weak → Eternal)
  - **Sillage** — 4 SVG wave arcs (Intimate → Enormous)
  - **Price Value** — 5 coin icons (Way Overpriced → Great Value)
  - **Season** — 4 season + day/night icons, normalized independently
- Description and link to Fragrantica

### Fragrance Map
- Perfumes grouped by dominant accord family
- Top 5 rated fragrances per accord, color-coded

### UI / UX
- Dark / light mode toggle (persisted to `localStorage`)
- Minimal black & white design with Cormorant Garamond serif headlines
- Fully responsive

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · Uvicorn |
| Frontend | Vanilla JS · CSS custom properties |
| Fonts | Cormorant Garamond · Jost (Google Fonts) |
| Data | Fragrantica (scraped via Selenium) |
| Deploy | Render.com |

---

## Project Structure

```
perfume_app/
├── app.py                    # FastAPI backend — API endpoints
├── selenium_scraper.py       # Core Fragrantica scraper
├── scrape_all_brands.py      # Scrape all brands entry point
├── update_vote_data.py       # Re-scrape / update vote fields
├── fix_descriptions.py       # Re-scrape truncated descriptions
├── fix_image_paths.py        # Fix image_local path mismatches
├── check_brands.py           # Audit brand completeness
├── missing_report.py         # Report missing data fields
├── audit_data.py             # Full dataset audit
├── retry_missing_votes.py    # Re-scrape incomplete vote data
├── fragrantica_perfumes.json # Main dataset (898 perfumes)
├── perfume_images/           # Local perfume photos (~900 PNGs)
├── perfume_notes/            # Local note images (scraping only)
├── static/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── requirements.txt
├── render.yaml
└── .gitignore
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | HTML app |
| GET | `/api/perfumes` | Paginated + filtered perfume list |
| GET | `/api/brands` | All brands with counts |
| GET | `/api/accords` | All accords sorted by frequency |
| GET | `/api/notes` | All unique notes (for autocomplete) |
| GET | `/api/stats` | Summary stats |
| GET | `/images/{filename}` | Static perfume images |

### `/api/perfumes` Query Parameters

| Parameter | Type | Description |
|---|---|---|
| `search` | string | Name or house substring |
| `brand` | string | Exact house name |
| `category` | string | `designer` / `niche` / `luxury` |
| `gender` | string | `men` / `women` / `unisex` |
| `note` | string | Any note substring |
| `accord` | string | Main accord substring |
| `season` | string | `spring` / `summer` / `fall` / `winter` |
| `longevity` | string | `very_weak` / `weak` / `moderate` / `long_lasting` / `eternal` |
| `sillage` | string | `intimate` / `moderate` / `strong` / `enormous` |
| `price` | string | `way_overpriced` / `overpriced` / `ok` / `good_value` / `great_value` |
| `sort` | string | `rating` / `votes` / `name` / `brand` / `year` |
| `order` | string | `asc` / `desc` |
| `page` | int | Page number (default: 1) |
| `limit` | int | Items per page (default: 24, max: 1000) |

> Season, longevity, sillage, and price filters sort results by the selected metric's **ratio within its own group** — not raw vote counts.

---

## Dataset

`fragrantica_perfumes.json` — 898 perfumes, each containing:

```json
{
  "name": "Sauvage",
  "brand": "Dior",
  "category": "designer",
  "gender": "men",
  "rating": 4.27,
  "votes": 98432,
  "release_year": 2015,
  "url": "https://www.fragrantica.com/...",
  "image_url": "https://...",
  "image_local": "perfume_images/Dior_Sauvage.png",
  "top_notes": ["Calabrian Bergamot", "Pepper"],
  "middle_notes": ["Lavender", "Pink Pepper", "Vetiver", "Patchouli", "Geranium"],
  "base_notes": ["Ambroxan", "Cedar", "Labdanum"],
  "main_accords": ["fresh spicy", "aromatic", "citrus", "woody", "fresh"],
  "longevity":   { "very_weak": 120, "weak": 380, "moderate": 2100, "long_lasting": 5800, "eternal": 980 },
  "sillage":     { "intimate": 210, "moderate": 3100, "strong": 4200, "enormous": 890 },
  "price_value": { "way_overpriced": 90, "overpriced": 420, "ok": 2800, "good_value": 1900, "great_value": 310 },
  "season":      { "spring": 2100, "summer": 3800, "fall": 1900, "winter": 800, "day": 5200, "night": 2100 },
  "description": "..."
}
```

---

## Running Locally

```bash
# 1. Create and activate a Python environment
conda create -n scent_env python=3.11
conda activate scent_env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn app:app --reload --port 5001

# 4. Open in browser
# http://localhost:5001
```

---

## Scraping

The dataset was built using `selenium_scraper.py` + `scrape_all_brands.py`.  
To re-scrape or extend the dataset:

```bash
# Scrape all brands from scratch
python scrape_all_brands.py

# Update vote data (longevity, sillage, price, season) for existing entries
python update_vote_data.py

# Re-scrape truncated descriptions
python fix_descriptions.py
```

> Scraping requires Google Chrome and ChromeDriver. The scraper uses `selenium-manager` for automatic driver management.

---

## Deploying to Render.com

1. Push to GitHub
2. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**
3. Connect the `perfume_app` repository
4. Render auto-detects `render.yaml` with:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service** — deploy takes ~2 minutes

> Free tier services sleep after 15 minutes of inactivity (cold start ~30s).

---

## License

Personal / educational project. Fragrance data sourced from [Fragrantica](https://www.fragrantica.com). Images belong to their respective brand owners.
