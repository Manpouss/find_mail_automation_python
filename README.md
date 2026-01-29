# Email Enricher (Public-Only)

Reusable Python script to enrich a CSV with **publicly visible** email addresses.

## What it does
Given an input CSV (e.g. TikTok creator exports), the script:
1) Extracts emails locally from `detected_emails` and `bio_text`.
2) For rows still missing an email, extracts external website URLs from `bio_links` (only explicit `http(s)` or `www.` links).
3) Optionally crawls a **small, limited** set of public pages per external website (homepage + a few “contact/privacy/about” links).
4) Outputs the same CSV enriched with:
   - `email`
   - `source_url` (exact page/field where the email was found)
   - `method` (`detected_emails` / `bio_text` / `crawl`)
   - `status` (`found` / `not_found` / `blocked`)
   - `confidence` (optional score)

### Public-only 
The script only reads publicly accessible content and does not attempt to access private data.

### Important note about crawling
External website crawling happens **only if a website URL is explicitly present in the `bio_links` column**.
This avoids guessing domains and keeps the process deterministic and scalable.

## Requirements
- Python 3.10+ (Windows/Mac/Linux)
- Packages: `pandas`, `requests`

## Setup
```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```
## Usage
Basic : 
```bash
python enrich.py input.csv
```

With separators (Excel-friendly output for FR):
```bash
python enrich.py input.csv --in-sep "," --out-sep ";"
```

Print detected external URLs:
```bash
python enrich.py input.csv --print-urls
```

Disable crawling (local extraction only):
```bash
python enrich.py input.csv --no-crawl

```

Tune crawl limits:
```bash
python enrich.py input.csv --timeout 10 --max-pages 3 --max-urls-per-row 2

```
## Performance notes (10k+ rows)
Works on large CSVs.

Total runtime depends mainly on the number of external websites and their response times.

Crawling is limited by --max-pages and --max-urls-per-row (safe defaults).

## Output columns
email: first valid public email found (blank if none)

source_url: exact page where email was found

method: detected_emails / bio_text / crawl

status: found / not_found / blocked

confidence: 1.0 (detected_emails), 0.8 (bio_text), 0.6 (crawl)