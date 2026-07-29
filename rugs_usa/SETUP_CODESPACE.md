# Codespace setup — RugsUSA practice

Target folder: `/workspaces/de-zoomcamp/rugs_usa`

## Step 1 — download these four files from the chat

- `rugsusa_practice.duckdb` (the database, ~5 MB)
- `q.py` (query runner)
- `PRACTICE_PROBLEMS.md` (10 drills + answers)
- `build_db.py` (regenerates the DB — backup if the upload misbehaves)

## Step 2 — get them into the Codespace

In VS Code, open the Explorer sidebar, expand `rugs_usa`, and **drag all four files from your local Downloads folder directly onto that folder**. VS Code uploads them into the Codespace.

If drag-and-drop doesn't take the `.duckdb` binary, skip it — upload only the three text files and rebuild the database in step 4.

## Step 3 — install DuckDB

Open a terminal in VS Code (`` Ctrl+` ``), then:

```bash
cd /workspaces/de-zoomcamp/rugs_usa
pip install duckdb
```

If `pip` complains about an externally-managed environment:
```bash
pip install duckdb --break-system-packages
```

## Step 4 — only if the .duckdb file didn't upload

```bash
python build_db.py
```

Takes a few seconds and writes `rugsusa_practice.duckdb` in the same folder. Deterministic — same seed, same data, same answers as the problem set.

## Step 5 — verify

```bash
python q.py "SELECT COUNT(*) FROM fct_order_lines"
```

Expect roughly 32,900. Then start practicing:

```bash
python q.py
```

Type SQL across multiple lines, hit **blank line** to run, `Ctrl+C` to quit.

---

## Working style that beats the REPL

Create `scratch.sql` in the folder and write your attempts there — you get syntax highlighting, and you can keep your work:

```bash
python q.py -f scratch.sql
```

Edit, save, re-run. Keeps a record of what you wrote, which matters more than it sounds: rereading your own attempts tomorrow morning is better revision than rereading my answers.

## Optional — notebook mode

If you prefer notebooks (you likely have the Jupyter extension already from Zoomcamp):

```bash
pip install jupysql pandas
```

New file `practice.ipynb`, first cell:

```python
%load_ext sql
%sql duckdb:///rugsusa_practice.duckdb
```

Then any cell:

```python
%%sql
SELECT collection, SUM(net_revenue) AS revenue
FROM fct_order_lines f
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY 1 ORDER BY 2 DESC
```

Results render as tables. Nice for the window-function drills where you want to eyeball a running total.

## Committing it

The folder sits inside your `de-zoomcamp` repo, so `git status` will show it. Either commit it as practice work, or add `rugs_usa/` to `.gitignore` to keep it out of your Zoomcamp history. Note the `.duckdb` file is binary — worth gitignoring even if you commit the scripts:

```
rugs_usa/*.duckdb
```

## If the Codespace was stopped

Codespaces stop after inactivity but `/workspaces` persists. Reopen it, and your files are still there — you may need to re-run `pip install duckdb` if the container was rebuilt (not just stopped).
