#!/usr/bin/env python3
"""Minimal Respekt EPUB downloader

Functions:
- get_issue_list(session, year) -> list of (id, kind, issue_number)
- download_by_id(session, issue_id, year, issue_num, kind)
- download_whole_year(session, year)
- download_latest(session, year=None)

Credentials: set RESPEKT_USERNAME and RESPEKT_PASSWORD env vars.
"""
from __future__ import annotations
import os
import sys
import json
import ssl
import smtplib
import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup

BASE = "https://www.respekt.cz"
API_LOGIN = BASE + "/api/login"
EPUB_API = BASE + "/api/downloadEPub?issueId={}"
EPUB_DIR = "epubs"

EMAIL = os.environ.get("RESPEKT_USERNAME")
PASSWORD = os.environ.get("RESPEKT_PASSWORD")
EMAIL_SENDER = os.environ.get("SENDER_EMAIL")
EMAIL_SENDER_PASSWORD = os.environ.get("SENDER_EMAIL_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))

def login(email: str, password: str) -> requests.Session:
    s = requests.Session()
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": BASE,
        "Referer": BASE + "/uzivatel/prihlaseni",
        "User-Agent": "Mozilla/5.0",
    }
    r = s.post(API_LOGIN, json={"email": email, "password": password}, headers=headers)
    r.raise_for_status()
    j = r.json()
    if not j.get("success"):
        raise SystemExit("Login failed")
    return s


def get_issue_list(session: requests.Session, year: int) -> List[Tuple[str, str, Optional[int]]]:
    """Return list of (id, kind, issue_number) from archive page's __NEXT_DATA__ JSON."""
    url = f"{BASE}/archiv/{year}"
    response = session.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script or not script.string:
        return []
    data = json.loads(script.string)
    props = data.get("props", {}).get("pageProps", {})
    issues = props.get("listIssue") or []
    out = []
    for it in issues:
        iid = it.get("id")
        kind = it.get("kind")
        inum = it.get("issue")
        if iid:
            out.append((iid, kind, inum))
    out = sorted(out, key=lambda x: (x[1], x[2], x[0])) ## order by kind, issue number, id
    return out


def download_by_id(session: requests.Session, issue_id: str, year: int, issue_num: Optional[int], kind: str, save_path: str = EPUB_DIR, override: bool = False) -> str | None:
    """Download EPUB and save with naming rules:
    - weekly: respekt_<year>_<week>.epub
    - other kinds: respekt_<kind>_<year>_<issue_num or id>.epub
    """
    year_dir = os.path.join(save_path, str(year))
    os.makedirs(year_dir, exist_ok=True)
    if kind == "weekly":
        if issue_num is None:
            fname = f"respekt_{year}_{issue_id}.epub"
        else:
            fname = f"respekt_{year}_{int(issue_num):02d}.epub"
    else:
        tail = issue_num if issue_num is not None else issue_id
        fname = f"respekt_{kind}_{year}_{tail}.epub"
    
    out_path = os.path.join(year_dir, fname)
    if os.path.exists(out_path):
        if override:
            ## when override is True, we will download and overwrite the existing file
            print("override exists:", out_path)
        else:
            ## otherwise, we skip downloading and return the existing path
            print("skip exists:", out_path)
            return out_path

    url = EPUB_API.format(issue_id)
    r = session.get(url, headers={"User-Agent": "Mozilla/5.0", "Referer": f"{BASE}/tydenik/{year}/{issue_num or ''}"}, stream=True)
    if r.status_code != 200:
        print("download failed", r.status_code, issue_id)
        return None
    
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)
    print("saved", out_path)
    return out_path


def download_whole_year(session: requests.Session, year: int, save_path: str = EPUB_DIR):
    items = get_issue_list(session, year)
    for iid, kind, inum in items:
        download_by_id(session, iid, year, inum, kind, save_path=save_path)


def download_latest(session: requests.Session, save_path: str = EPUB_DIR) -> Optional[str]:
    year = date.today().year
    items = get_issue_list(session, year)
    weekly = [it for it in items if it[1] == "weekly"]
    if not weekly:
        raise SystemExit("No weekly issues found for year")
    iid, kind, inum = weekly[-1]
    return download_by_id(session, iid, year, inum, kind, save_path=save_path, override=True)

def send_latest_issue(recipients: str, attachment_path: str | None = None, kindle: bool = False):
    """
    Send HTML report to recipients (semicolon-separated). Optionally attach a file (EPUB).
    - recipients: 'a@x.com;b@y.com;c@z.com'
    - attachment_path: path to EPUB file (optional)
    """
    port = SMTP_PORT
    smtp_server = SMTP_SERVER

    if not EMAIL_SENDER or not EMAIL_SENDER_PASSWORD:
        print("Sender credentials not provided (env SENDER_EMAIL / SENDER_EMAIL_PASSWORD or args). Skipping email.")
        return

    # parse recipients
    to_list = [r.strip() for r in recipients.split(';') if r.strip()]
    if not to_list:
        print("No recipients provided. Skipping email.")
        return

    if kindle and len(to_list) > 1:
        raise ValueError("For Kindle, only one recipient per call is allowed.")
        return

    message = MIMEMultipart("alternative")
    message["From"] = EMAIL_SENDER
    if kindle:
        message["To"] = to_list[0]
        body = ""
    else:
        message["Subject"] = "Respekt - Aktuální vydání"
        message["To"] = EMAIL_SENDER    
        body = "<h1>Respekt - Aktuální vydání</h1><p>V příloze najdeš nejnovější vydání časopisu Respekt. Příjemné čtení!</p>"
        
    message.attach(MIMEText(body, "html"))

    # attach file if present
    if attachment_path and os.path.exists(attachment_path):
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(attachment_path, "rb") as fp:
            part = MIMEBase(maintype, subtype)
            part.set_payload(fp.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(attachment_path)}"',
        )
        message.attach(part)
    else:
        print("Attachment path not provided or file does not exist. Aborting email.")
        return

    # send
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_SENDER_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_list, message.as_string())
        print(f"Email sent with file {attachment_path} to {', '.join(to_list)}")
    except Exception as e:
        print("Error sending email:", e)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--year-from", type=int, help="start year for downloading whole years")
    p.add_argument("--year-to", type=int, help="end year for downloading whole years")
    p.add_argument("--latest", action="store_true", help="download latest weekly")
    p.add_argument("--save-path", type=str, default=EPUB_DIR, help="directory to save EPUBs")
    p.add_argument("--recipients", type=str, help="semicolon-separated email recipients for latest issue")
    p.add_argument("--kindle-recipients", type=str, help="semicolon-separated email recipients for latest issue (for Kindle)")
    args = p.parse_args()
    
    if not EMAIL or not PASSWORD:
        raise SystemExit("Set RESPEKT_USERNAME and RESPEKT_PASSWORD environment variables.")
    
    session = login(EMAIL, PASSWORD)
    if args.latest:
        path = download_latest(session, save_path=args.save_path)
        if path:
            send_latest_issue(recipients=args.recipients, attachment_path=path, kindle=False)
        if args.kindle_recipients:
            for recipient in args.kindle_recipients.split(';'):
                send_latest_issue(recipients=recipient.strip(), attachment_path=path, kindle=True)
    elif args.year_from and args.year_to:
        # pass save_path through a simple wrapper
        for year in range(args.year_from, args.year_to + 1):
            items = get_issue_list(session, year)
            for iid, kind, inum in items:
                download_by_id(session, iid, year, inum, kind, save_path=args.save_path, override=True)
    else:
        raise SystemExit("Please provide --latest or both --year-from and --year-to arguments.")

if __name__ == "__main__":
    main()
