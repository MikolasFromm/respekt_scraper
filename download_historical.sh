#!/bin/bash
# Download historical issues for a range of years.
# Set the required environment variables before running:
#   export RESPEKT_USERNAME='your@email.com'
#   export RESPEKT_PASSWORD='yourpassword'
#
# SENDER_EMAIL / SENDER_EMAIL_PASSWORD are not needed for bulk downloads.

SAVE_PATH="${SAVE_PATH:-./epubs}"
YEAR_FROM="${YEAR_FROM:-2023}"
YEAR_TO="${YEAR_TO:-2023}"

source .venv/bin/activate
python3 respekt_scraper.py \
  --year-from "$YEAR_FROM" \
  --year-to "$YEAR_TO" \
  --save-path "$SAVE_PATH"
