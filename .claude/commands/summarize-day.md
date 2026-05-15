Summarize everything I've worked on today by reading my Claude Code session logs, GitHub activity, Jira tickets, and Confluence pages, then write it to my work log.

## Step 1: Find today's sessions

Run:
```
find ~/.claude/projects/ -name "*.jsonl" -maxdepth 2 -newermt "$(date +%Y-%m-%d)" 2>/dev/null
```

## Step 2: Read and summarize each session

For each file found, read it and extract what was worked on — look at user messages and assistant tool calls (file edits, bash commands, tool results) to understand the work. Group by project (derived from the directory name, e.g. `-Users-mcollins-projects-sre-chef` → `sre-chef`).

## Step 3: Check GitHub PRs merged today

Run:
```
gh pr list --author @me --state merged --search "merged:$(date +%Y-%m-%d)" --limit 20 --json number,title,url,repository 2>/dev/null
```

Note any PRs merged. If the command returns no results, also try:
```
gh search prs --author @me --merged --merged-after $(date +%Y-%m-%d) --limit 20 --json number,title,url,repository 2>/dev/null
```

## Step 4: Check Jira activity today

Use `searchJiraIssuesUsingJql` with JQL to find tickets that had any status change today:
```
assignee = currentUser() AND status changed DURING (startOfDay(), endOfDay()) ORDER BY updated DESC
```

This captures the full picture of work in flight — tickets moved to in-progress, in-review, done, etc. Note the ticket keys, summaries, and what status they moved to.

## Step 5: Check Confluence pages updated today

Use `searchConfluenceUsingCql` with CQL:
```
contributor = currentUser() AND lastModified >= startOfDay() ORDER BY lastModified DESC
```

Note any pages created or updated, their titles and spaces.

## Step 6: Write to the work log

Run `./log.py` from `~/projects/sre/work-log` to create the entry if it doesn't exist. The output will include the file path (e.g. `Created entry: ...` or `Entry already exists: ...`) — use that path to open and append the summary under today's day heading.

Write in the same casual, first-person style as existing entries. Guidelines based on past entries:
- Short declarative sentences, no bullet points, like documenting your day to a colleague
- Lead with what was done, add context only if important
- Name specific tools, people, and environments (stg, prod, etc.); be vague on volume ("a bunch of", "a few")
- Vary wording on how topics connect — "Also", "Plus", "After that", "Spent the rest of the day" — avoid repitition 
- It's fine to mention if something was painful, confusing, or took longer than expected
- Honest uncertainty is fine — "Pretty sure", "I think", "Not sure why" feel natural here
- Don't pad it out — a sentence or two is fine for a light day
- No corporate language, no impact statements, no stand-up format — just what happened

After writing, run `./log.py -e` from `~/projects/sre/work-log` to open the file in the editor for review. This will commit and push automatically when the editor is closed.
