Summarize everything I've worked on by reading my Claude Code session logs, GitHub activity, Jira tickets, and Confluence pages, then write it to my work log.

## Determine target date

If `$ARGUMENTS` is provided and non-empty, use it as the target date (format: YYYY-MM-DD). Otherwise use today's date from `date +%Y-%m-%d`.

Call this value TARGET_DATE throughout all steps below.

## Step 1: Find sessions for target date

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

## Step 2: Read and summarize each session

For each file found, read it and extract what was worked on — look at user messages and assistant tool calls (file edits, bash commands, tool results) to understand the work. Group by project (derived from the directory name, e.g. `-Users-mcollins-projects-sre-chef` → `sre-chef`).

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

Before writing anything, present a numbered list of every distinct activity found across all sources — sessions, PRs, Jira, and Confluence. Group loosely by theme or ticket if there are natural clusters. For each item include the source (e.g. `[session]`, `[PR]`, `[Jira]`, `[Confluence]`) and a one-line description.

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
