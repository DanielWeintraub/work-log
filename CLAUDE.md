# Work Log

Daily work log using a fiscal year/quarter/week directory structure.

## Structure

```
FY{year}/Q{quarter}/W{number} - {start_date} to {end_date}.md
```

- **Fiscal year** ends January 31st (FY2027 = Feb 1 2026 – Jan 31 2027)
- **Quarters:** Q1: Feb–Apr, Q2: May–Jul, Q3: Aug–Oct, Q4: Nov–Jan
- **Weeks** are numbered within each quarter, Monday–Friday

## Usage

- `./log.py` — create entry for the current week, commit, and push
- `./log.py --date YYYY-MM-DD` — create entry for a specific date's week
- `./log.py -e` — create/open entry in editor, commit and push on close
- `./log.py --git-only` — just commit and push existing changes
- `./log.py --no-push` — commit without pushing

## Entry Format

Each weekly file has day-of-week headings (Monday–Friday). Add brief, natural notes under the current day describing what was worked on. See existing entries for tone and style.

## Updating the Log

To add a note for today, open the current week's file and append under the correct day heading. If the file doesn't exist yet, run `./log.py` first to create it. After editing, run `./log.py --git-only` to commit and push.
