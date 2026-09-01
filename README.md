# Internship Portal Checker

Checks a list of internship pages (specific companies + general boards like
Internshala) and tells you via Telegram when a status flips between OPEN and
CLOSED. Run it manually whenever you want a check — no scheduler required.

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Create a Telegram bot (2 minutes)

1. Open Telegram, search for **@BotFather**, send `/newbot`.
2. Follow the prompts (pick a name and a username ending in `bot`).
3. BotFather gives you a **bot token** like `123456:ABC-DEF...`. Copy it.
4. Send your new bot any message (e.g. "hi") so it can message you back.
5. Get your **chat_id** by visiting this URL in your browser (replace the token):
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Look for `"chat":{"id": ...}` in the response — that number is your chat_id.

Put both values into `config.json`:

```json
"telegram": {
  "bot_token": "123456:ABC-DEF...",
  "chat_id": "987654321"
}
```

## 3. Configure what to track

Edit `config.json`. Two kinds of sources:

**A. Specific company page** (keyword-based) — good for pages that literally
say "Applications open" / "Applications closed" somewhere on the page:

```json
{
  "name": "Google STEP Internship",
  "url": "https://buildyourfuture.withgoogle.com/programs/step/",
  "open_keywords": ["applications are open", "apply now"],
  "closed_keywords": ["applications are closed", "no longer accepting"]
}
```

Tip: open the page, Ctrl+F for the actual wording it uses, and put that
phrase (lowercase) into the right keyword list. Keyword matching is
case-insensitive.

**B. Listing/search page** (count-based) — good for boards like Internshala
where "open" really means "listings currently exist for this search":

```json
{
  "name": "Internshala - Data Science internships",
  "url": "https://internshala.com/internships/data-science-internship/",
  "mode": "count_listings"
}
```

You can add as many sources as you like, mixing both modes.

## 4. Run it

```bash
python checker.py
```

First run just saves a baseline (no notification, since there's nothing to
compare against yet). From the second run onward, if a source's status
flipped since last time, you get a Telegram ping. State is stored in
`state.json` next to the script — don't delete it unless you want to reset
the baseline.

## Notes & limitations

- This works by reading the public HTML of a page. Some sites render content
  with JavaScript, which plain `requests` won't execute — if a source always
  comes back `UNKNOWN`, that's likely why (would need a headless browser like
  Playwright for those; happy to extend it if you hit this).
- LinkedIn specifically blocks most scraping and requires login for job
  search results, so it's not a good candidate for this approach — Internshala
  and direct company career pages work much better.
- Respect each site's `robots.txt` / terms of use, and don't hammer sites with
  very frequent requests — a few checks a day is plenty for internship cycles.
- Since you're running this manually, consider just running it once a day
  when you check in.