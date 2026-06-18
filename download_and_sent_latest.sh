#!/bin/bash
# Download the latest weekly issue and email it to recipients.
# Set the required environment variables before running:
#   export RESPEKT_USERNAME='your@email.com'
#   export RESPEKT_PASSWORD='yourpassword'
#   export SENDER_EMAIL='your-sender@example.com'
#   export SENDER_EMAIL_PASSWORD='yourpassword'
#   export RECIPIENTS='recipient1@example.com;recipient2@example.com'

#   export SMTP_SERVER='smtp.example.com'              # optional, default: smtp.gmail.com
#   export SMTP_PORT='465'                             # optional, default: 465
#   export KINDLE_RECIPIENTS='yourkindle@kindle.com'   # optional
#   export SAVE_PATH='/path/to/save/epubs'             # optional, default: ./epubs

SAVE_PATH="${SAVE_PATH:-./epubs}"

source .venv/bin/activate
python3 respekt_scraper.py \
  --latest \
  --save-path "$SAVE_PATH" \
  ${RECIPIENTS:+--recipients "$RECIPIENTS"} \
  ${KINDLE_RECIPIENTS:+--kindle-recipients "$KINDLE_RECIPIENTS"}
