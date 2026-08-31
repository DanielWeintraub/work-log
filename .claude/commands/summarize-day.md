Summarize everything I've worked on by reading my Claude Code session logs, GitHub activity, Jira tickets, and Confluence pages, then write it to my work log.

## Determine target date

If `$ARGUMENTS` is provided and non-empty, use it as the target date (format: YYYY-MM-DD). Otherwise use today's date from `date +%Y-%m-%d`.

Call this value TARGET_DATE throughout all steps below.

## Step 1: Find candidate session files

If TARGET_DATE is today, run:
```
find ~/.claude/projects/ -name "*.jsonl" -maxdepth 2 -newermt "TARGET_DATE" 2>/dev/null
```

If TARGET_DATE is a past date, bound the range to that day only by running:
```
find ~/.claude/projects/ -name "*.jsonl" -maxdepth 2 \
  -newermt "TARGET_DATE" \
  ! -newermt "$(date -v+1d -f "%Y-%m-%d" "TARGET_DATE" +%Y-%m-%d)" \
  2>/dev/null
```

**This is a candidate list only, based on file mtime — it is not reliable on its own.** Claude Code session files are resumable and often span many days; a file can be touched (mtime bumped) on TARGET_DATE while almost all of its actual content — and sometimes *all* of it — belongs to earlier days. Never treat a file appearing here as proof that work happened on TARGET_DATE. Every file must be verified against its actual message timestamps in Step 2 before anything from it is included.

## Step 2: Verify each candidate's actual dates, then summarize only TARGET_DATE content

For each candidate file, first check which dates its messages actually fall on:
```
python3.14 -c "
import json
path = '<file>'
dates = {}
with open(path) as fh:
    for line in fh:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        ts = obj.get('timestamp')
        if ts:
            d = ts[:10]
            dates[d] = dates.get(d, 0) + 1
for d in sorted(dates):
    print(d, dates[d])
"
```

- If TARGET_DATE has zero matching entries, **discard the file entirely** — the mtime was misleading (e.g. a resumed session with no real new content, or a metadata-only touch). Do not summarize anything from it.
- If TARGET_DATE has some matching entries but the file also has entries from other days, only read and summarize the entries whose timestamp starts with TARGET_DATE. Ignore the rest, even if it's the bulk of the file — a long-running session's earlier days are out of scope for this run (they should already be reflected in that earlier day's log entry, or are a separate backfill question).

When delegating file reads to a subagent (e.g. for large files), give it TARGET_DATE explicitly and instruct it to: (a) run the per-file date-count check above first, (b) state how many entries matched TARGET_DATE before summarizing anything, (c) summarize only those matching entries, and (d) report back "no activity on TARGET_DATE" rather than silently substituting nearby days' content if the count is zero. Do not just tell it "this session is from TARGET_DATE" — let it verify that independently, since the premise may be wrong.

Group surviving activity by project (derived from the directory name, e.g. `-Users-mcollins-projects-sre-chef` → `sre-chef`).

## Step 3: Check GitHub PRs merged on target date

If TARGET_DATE is today, run:
```
gh search prs --author @me --merged --merged-at ">=TARGET_DATE" --limit 20 --json number,title,url,repository 2>/dev/null
```

If TARGET_DATE is a past date, run:
```
gh search prs --author @me --merged --merged-at "TARGET_DATE..TARGET_DATE" --limit 20 --json number,title,url,repository 2>/dev/null
```

Note any PRs merged.

## Step 3b: Check PR reviews left on target date

The search above only catches PRs you authored/merged — it misses reviews you left on other people's PRs. Get your GitHub login, then search for PRs with review activity touching TARGET_DATE:
```
gh api user --jq .login
gh api "search/issues?q=type:pr+reviewed-by:@me+updated:TARGET_DATE" --jq '.items[] | .repository_url + " " + (.number|tostring)'
```

This search is noisy: `updated_at` reflects the PR's last update, not necessarily when you reviewed it — a PR you reviewed months or years ago can still match if something else touched it on TARGET_DATE. Do not trust it on its own. For each candidate PR, confirm you actually reviewed it on TARGET_DATE by checking the real review timestamps:
```
gh api repos/{owner}/{repo}/pulls/{number}/reviews --jq '.[] | select(.user.login=="YOUR_LOGIN" and (.submitted_at | startswith("TARGET_DATE"))) | {state, submitted_at, body}'
```

Discard any candidate with no matching review on TARGET_DATE. For ones that match, also pull your line comments from that date for context on what was actually flagged:
```
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq '.[] | select(.user.login=="YOUR_LOGIN" and (.created_at | startswith("TARGET_DATE"))) | {path, body}'
```

Note the PR title, review state (APPROVED/COMMENTED/CHANGES_REQUESTED), review body, and any line-comment context — tag these `[PR review]`.

## Step 4: Check Jira activity on target date

Use `searchJiraIssuesUsingJql` with JQL to find tickets whose status was changed by the current user on TARGET_DATE. Compute NEXT_DAY (TARGET_DATE + 1 day) and use:
```
status changed BY currentUser() DURING ("TARGET_DATE", "NEXT_DAY") ORDER BY updated DESC
```

Note the ticket keys, summaries, and what status they moved to.

## Step 5: Check Confluence pages updated on target date

Use `searchConfluenceUsingCql` with CQL. For today use:
```
contributor = currentUser() AND lastModified >= startOfDay() ORDER BY lastModified DESC
```

For a past date, compute NEXT_DAY (TARGET_DATE + 1 day) and use:
```
contributor = currentUser() AND lastModified >= "TARGET_DATE" AND lastModified < "NEXT_DAY" ORDER BY lastModified DESC
```

For each page returned, call `getConfluencePage` to fetch its details and check the `version.by.displayName` field (the last editor). Only include the page if the last editor is Dan Weintraub. Silently discard pages last edited by someone else — `contributor` matches viewers and commenters too, not just editors.

## Step 6: Present options and confirm

Before writing anything, present a numbered list of every distinct activity found across all sources — sessions, PRs, PR reviews, Jira, and Confluence. Group loosely by theme or ticket if there are natural clusters. For each item include the source (e.g. `[session]`, `[PR]`, `[PR review]`, `[Jira]`, `[Confluence]`) and a one-line description.

Ask the user which items to include. Wait for their response before proceeding.

## Step 7: Offer to create Jira tickets for untracked work

From the confirmed list, identify activities that have no associated Jira ticket — i.e., items tagged `[session]`, `[PR]`, or `[Confluence]` that don't reference a CORE-XXXX key.

If any exist, list them and ask: "Any of these need a Jira ticket?" Wait for the user's response before proceeding.

If the user wants tickets created, use `createJiraIssue` for each:
- `cloudId`: `93c1a38e-41b0-4549-9bcb-7a3330a3361b`
- `projectKey`: CORE
- `issueTypeName`: Task
- `assignee_account_id`: `6179978f20972200713455e1`
- `contentFormat`: `adf` — description must be a proper ADF JSON document
- `customfield_16588`: infer the type of work from context (Unplanned - Cross-Team Request, Unplanned - Reactive Maintenance, Planned - Engineering Roadmap, etc.)
- Infer a concise summary and description from the activity context

If no untracked activities exist, skip silently.

## Step 8: Write to the work log

If TARGET_DATE is today, run `./log.py` from `~/git/work-log` to create the entry if it doesn't exist.
If TARGET_DATE is a past date, run `./log.py --date TARGET_DATE` from `~/git/work-log`.

The output will include the file path (e.g. `Created entry: ...` or `Entry already exists: ...`) — use that path to open and append the summary under the correct day heading.

Write in the same casual, first-person style as existing entries. Guidelines based on past entries:
- Short declarative sentences, no bullet points, like documenting your day to a colleague
- Lead with what was done, add context only if important
- Name specific tools, people, and environments (stg, prod, etc.); be vague on volume ("a bunch of", "a few")
- Vary wording on how topics connect — "Also", "Plus", "After that", "Spent the rest of the day" — avoid repitition 
- It's fine to mention if something was painful, confusing, or took longer than expected
- Honest uncertainty is fine — "Pretty sure", "I think", "Not sure why" feel natural here
- Don't pad it out — a sentence or two is fine for a light day
- No corporate language, no impact statements, no stand-up format — just what happened

After writing, run `./log.py -e` from `~/git/work-log` to open the file in the editor for review. This will commit and push automatically when the editor is closed.
