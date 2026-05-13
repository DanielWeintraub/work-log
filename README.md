# Work Log

A Python script to manage a work log with an automated fiscal year/quarter/week directory structure.

## Directory Structure

The script creates files following this pattern:
```
FY{year}/Q{quarter}/W{number} - {date_range}.md
```

Example:
```
FY2027/Q1/W02 - 2026-02-09 to 2026-02-13.md
```

**Fiscal Year:** Ends on January 31st
- FY2027 = February 1, 2026 - January 31, 2027

**Quarters:**
- Q1: Feb 1 - Apr 30
- Q2: May 1 - Jul 31
- Q3: Aug 1 - Oct 31
- Q4: Nov 1 - Jan 31

**Weeks:** Numbered within each quarter (Monday-Friday)

## Usage

### Create an entry for today
```bash
./log.py
```

This will:
1. Create the directory structure if it doesn't exist
2. Create a new markdown file with today's date
3. Add a header with the date range and fiscal year info
4. Git add, commit, and push the changes

### Create an entry for a specific date
```bash
./log.py --date 2026-03-15
```

### Custom commit message
```bash
./log.py -m "Weekly review"
```

### Skip git push
```bash
./log.py --no-push
```

### Edit in VS Code and sync after closing
```bash
./log.py --edit
# or
./log.py -e
```

This will:
1. Create/open the log entry
2. Open it in VS Code and wait for you to close the editor
3. Git add, commit, and push your changes

### Only commit and push (no new entry)
```bash
./log.py --git-only
```

## Entry Format

Each entry includes a header with the week date range, fiscal year info, and day-of-week headings:

```markdown
# Work Log - 2026-02-09 to 2026-02-13

**Fiscal Year:** FY2027 Q1 Week 3

---

## Notes

### Monday

### Tuesday

### Wednesday

### Thursday

### Friday
```

## Requirements

- Python 3.6+
- Git

## Examples

```bash
# Create today's entry and push to origin
./log.py

# Edit today's entry in VS Code, then auto-sync when done
./log.py --edit

# Create entry for specific date with custom message
./log.py --date 2026-02-15 -m "Sprint planning"

# Edit and sync entry for specific date
./log.py --date 2026-02-15 --edit

# Create entry but don't push yet
./log.py --no-push

# Just commit and push existing changes
./log.py --git-only -m "Updated previous entries"
```
