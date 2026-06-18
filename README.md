# Respekt EPUB Downloader

A minimal Python scraper that downloads weekly issues of the Czech magazine [Respekt](https://www.respekt.cz) as EPUB files and optionally emails them (including to Kindle).

## Features

- Download a single latest weekly issue
- Bulk-download all issues for a range of years
- Send the downloaded EPUB to any number of email recipients
- Kindle delivery support (one address per send)

## Requirements

- Python 3.9+
- A valid Respekt subscription

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

All credentials and settings are passed via environment variables — never hardcode them in the scripts.

| Variable | Required | Description |
|---|---|---|
| `RESPEKT_USERNAME` | yes | Your Respekt account email |
| `RESPEKT_PASSWORD` | yes | Your Respekt account password |
| `SENDER_EMAIL` | for email | The address emails are sent from |
| `SENDER_EMAIL_PASSWORD` | for email | SMTP password for the sender account |
| `SMTP_SERVER` | no | SMTP host (default: `smtp.gmail.com`) |
| `SMTP_PORT` | no | SMTP port for SSL (default: `465`) |

Export them in your shell or put them in a `.env` file (which is gitignored):

```bash
export RESPEKT_USERNAME='your@email.com'
export RESPEKT_PASSWORD='yourpassword'
export SENDER_EMAIL='sender@example.com'
export SENDER_EMAIL_PASSWORD='yourpassword'
```

## Usage

### Download the latest weekly issue

```bash
python3 respekt_scraper.py --latest
```

### Download and email the latest issue

```bash
python3 respekt_scraper.py \
  --latest \
  --recipients 'alice@example.com;bob@example.com'
```

### Send to Kindle

```bash
python3 respekt_scraper.py \
  --latest \
  --kindle-recipients 'yourkindle@kindle.com'
```

### Download historical issues (bulk)

```bash
python3 respekt_scraper.py --year-from 2020 --year-to 2024
```

### Custom save directory

Pass `--save-path` to any command:

```bash
python3 respekt_scraper.py --latest --save-path /path/to/my/epubs
```

EPUBs are saved under `<save-path>/<year>/` with names like `respekt_2024_42.epub` (weekly) or `respekt_special_2024_1.epub` (other kinds).

## Shell helper scripts

Two ready-made scripts are included:

| Script | Purpose |
|---|---|
| `download_and_sent_latest.sh` | Download the newest issue and email it |
| `download_historical.sh` | Bulk-download a year range |

Configure them via the env vars listed above plus:

| Variable | Default | Description |
|---|---|---|
| `SAVE_PATH` | `./epubs` | Where to store downloaded files |
| `RECIPIENTS` | — | Semicolon-separated email recipients |
| `KINDLE_RECIPIENTS` | — | Semicolon-separated Kindle addresses |
| `YEAR_FROM` / `YEAR_TO` | `2023` | Year range for bulk download |

### Automating with cron

```cron
# Every Wednesday at 07:00
0 7 * * 3 RESPEKT_USERNAME=... RESPEKT_PASSWORD=... ... /path/to/download_and_sent_latest.sh
```

Or source a `.env` file at the top of the script before running it.

## License

Apache 2.0
