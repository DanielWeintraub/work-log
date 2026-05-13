#!/usr/bin/env python3
"""
Work Log Manager

Manages work log entries with fiscal year/quarter/week structure.
Fiscal year ends on January 31st.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import argparse

# Script directory for absolute paths
SCRIPT_DIR = Path(__file__).parent


def get_fiscal_year(date):
    """Get fiscal year for a given date. FY ends on Jan 31."""
    if date.month == 1:
        return date.year
    else:
        return date.year + 1


def get_fiscal_year_start(fiscal_year):
    """Get the start date of a fiscal year."""
    return datetime(fiscal_year - 1, 2, 1)


def get_fiscal_quarter(date):
    """
    Get fiscal quarter (Q1-Q4) for a given date.
    Q1: Feb 1 - Apr 30
    Q2: May 1 - Jul 31
    Q3: Aug 1 - Oct 31
    Q4: Nov 1 - Jan 31
    """
    month = date.month
    if month in [2, 3, 4]:
        return "Q1"
    elif month in [5, 6, 7]:
        return "Q2"
    elif month in [8, 9, 10]:
        return "Q3"
    else:  # 11, 12, 1
        return "Q4"


def get_week_start(date):
    """Get the Monday of the week for a given date."""
    return date - timedelta(days=date.weekday())


def get_week_number_in_quarter(date):
    """Get the week number within the fiscal quarter."""
    quarter = get_fiscal_quarter(date)
    fiscal_year = get_fiscal_year(date)

    # Determine quarter start date
    if quarter == "Q1":
        quarter_start = datetime(fiscal_year - 1, 2, 1)
    elif quarter == "Q2":
        quarter_start = datetime(fiscal_year - 1, 5, 1)
    elif quarter == "Q3":
        quarter_start = datetime(fiscal_year - 1, 8, 1)
    else:  # Q4
        quarter_start = datetime(fiscal_year - 1, 11, 1)

    # Get the Monday of the week containing the date
    week_start = get_week_start(date)

    # Find the first Monday >= quarter_start (start of week 1)
    days_until_monday = (7 - quarter_start.weekday()) % 7
    quarter_first_monday = quarter_start + timedelta(days=days_until_monday)

    # Calculate week number (1-indexed)
    week_number = ((week_start - quarter_first_monday).days // 7) + 1

    return week_number


def get_week_date_range(date):
    """Get the date range (Monday-Friday) for a given date's week."""
    week_start = get_week_start(date)
    week_end = week_start + timedelta(days=4)  # Friday
    return week_start, week_end


def create_note(date=None):
    """Create a new work log entry for the week with date range header."""
    if date is None:
        date = datetime.now()

    # Use the week's Monday for quarter/FY classification so that weeks
    # spanning a quarter boundary stay in the quarter where they started.
    week_start = get_week_start(date)
    fiscal_year = get_fiscal_year(week_start)
    quarter = get_fiscal_quarter(week_start)
    week_number = get_week_number_in_quarter(week_start)

    # Get week date range
    week_start, week_end = get_week_date_range(date)
    date_range = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"

    # Create directory path (just FY/Quarter)
    dir_path = SCRIPT_DIR / f"FY{fiscal_year}/{quarter}"
    dir_path.mkdir(parents=True, exist_ok=True)

    # Create log entry file with week number and date range
    note_filename = f"W{week_number:02d} - {date_range}.md"
    note_path = dir_path / note_filename

    # Check if entry already exists
    if note_path.exists():
        print(f"Entry already exists: {note_path}")
        return note_path

    # Create entry with header
    header = f"""# Work Log - {date_range}

**Fiscal Year:** FY{fiscal_year} {quarter} Week {week_number}

---

## Notes

### Monday



### Tuesday



### Wednesday



### Thursday



### Friday


"""

    note_path.write_text(header)
    print(f"Created entry: {note_path}")

    return note_path


def generate_commit_message():
    """Generate a descriptive commit message based on staged changes."""
    import re

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        cwd=SCRIPT_DIR, capture_output=True, text=True
    )
    if not result.stdout.strip():
        return f"Update work log - {datetime.now().strftime('%Y-%m-%d')}"

    lines = result.stdout.strip().splitlines()
    added = []
    modified = []
    for line in lines:
        parts = line.split("\t", 1)
        if len(parts) == 2:
            status, filepath = parts
            if status == "A":
                added.append(filepath)
            else:
                modified.append(filepath)

    # Extract week identifiers from filenames (e.g. "FY2027/Q2/W01 - 2026-05-04 to 2026-05-08.md")
    def week_label(filepath):
        name = Path(filepath).stem  # e.g. "W01 - 2026-05-04 to 2026-05-08"
        parent = Path(filepath).parent.name  # e.g. "Q2"
        match = re.match(r"(W\d+)", name)
        week = match.group(1) if match else name
        return f"{parent}/{week}"

    # For modified files, check which days had content added
    def changed_days(filepath):
        diff = subprocess.run(
            ["git", "diff", "--cached", "-U0", str(filepath)],
            cwd=SCRIPT_DIR, capture_output=True, text=True
        )
        days = []
        for m in re.finditer(r"^\+### (\w+)", diff.stdout, re.MULTILINE):
            days.append(m.group(1))
        # Also check context around additions for day headings
        current_day = None
        for line in diff.stdout.splitlines():
            heading = re.match(r"^[\s@].*### (\w+)", line) or re.match(r"^ ### (\w+)", line)
            if heading:
                current_day = heading.group(1)
            # Look at @@ lines for context
            hunk = re.match(r"^@@.*@@\s*### (\w+)", line)
            if hunk:
                current_day = hunk.group(1)
            if line.startswith("+") and not line.startswith("+++") and current_day and current_day not in days:
                days.append(current_day)
        return days

    parts = []
    if added:
        labels = [week_label(f) for f in added if f.endswith(".md")]
        if labels:
            parts.append(f"Create work log {', '.join(labels)}")
    if modified:
        for f in modified:
            if not f.endswith(".md"):
                continue
            days = changed_days(f)
            label = week_label(f)
            if days:
                parts.append(f"Update {label} - {', '.join(days)}")
            else:
                parts.append(f"Update {label}")

    if not parts:
        # Fallback for non-log file changes
        return f"Update work log - {datetime.now().strftime('%Y-%m-%d')}"

    return "; ".join(parts)


def git_commit_and_push(message=None, auto_push=True):
    """Add, commit, and optionally push changes to git."""
    try:
        # Only stage work log entries (FY*/Q*/*.md), not scripts or other files
        log_files = list(SCRIPT_DIR.glob("FY*/Q*/*.md"))
        if not log_files:
            print("No work log files to stage.")
            return
        subprocess.run(["git", "add", "--"] + [str(f) for f in log_files], cwd=SCRIPT_DIR, check=True)

        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=SCRIPT_DIR,
            capture_output=True
        )

        if result.returncode == 0:
            print("No changes to commit.")
        else:
            # Generate message from staged diff if not provided
            if message is None:
                message = generate_commit_message()
            # Git commit
            subprocess.run(["git", "commit", "-m", message], cwd=SCRIPT_DIR, check=True)
            print(f"Committed changes: {message}")

        # Git push (regardless of whether we committed)
        if auto_push:
            # Check if there are unpushed commits
            result = subprocess.run(
                ["git", "rev-list", "@{u}..HEAD"],
                cwd=SCRIPT_DIR,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                subprocess.run(["git", "push", "origin", "main"], cwd=SCRIPT_DIR, check=True)
                print("Pushed to origin/main")
            else:
                print("Already up to date with origin/main")

    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Manage work log with fiscal year structure"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date for the entry (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--message", "-m",
        type=str,
        help="Git commit message. Default: auto-generated"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Don't push to origin after commit"
    )
    parser.add_argument(
        "--git-only",
        action="store_true",
        help="Only run git commit and push (don't create entry)"
    )
    parser.add_argument(
        "--edit", "-e",
        action="store_true",
        help="Open note in VS Code and wait for editor to close before syncing"
    )

    args = parser.parse_args()

    # Parse date if provided
    date = None
    if args.date:
        try:
            date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Handle git-only mode
    if args.git_only:
        git_commit_and_push(message=args.message, auto_push=not args.no_push)
        return

    # Create note
    note_path = create_note(date=date)

    # Open in editor if requested
    if args.edit:
        print(f"\nOpening in VS Code: {note_path}")
        try:
            subprocess.run(["code", "--wait", str(note_path)], check=True)
            print("Editor closed.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to open VS Code: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("VS Code 'code' command not found. Make sure VS Code is installed and 'code' is in your PATH.")
            sys.exit(1)

    # Git operations
    git_commit_and_push(message=args.message, auto_push=not args.no_push)

    print(f"\nEntry ready at: {note_path}")


if __name__ == "__main__":
    main()
