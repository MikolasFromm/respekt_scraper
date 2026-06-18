#!/bin/bash

YEAR_FROM="2023"
YEAR_TO="2025"

source .env
source .venv/bin/activate
python3 respekt_scraper.py \
  --year-from "$YEAR_FROM" \
  --year-to "$YEAR_TO" \
  --save-path "$SAVE_PATH"
