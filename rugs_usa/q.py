#!/usr/bin/env python3
"""
RugsUSA practice query runner.

Usage:
    python q.py "SELECT * FROM dim_product LIMIT 5"
    python q.py -f myquery.sql
    python q.py                      # interactive mode, blank line to run

Requires: pip install duckdb
"""
import sys, os, duckdb

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rugsusa_practice.duckdb")


def run(con, sql):
    sql = sql.strip().rstrip(";")
    if not sql:
        return
    try:
        con.execute(sql)
        cols = [d[0] for d in con.description] if con.description else []
        rows = con.fetchall()
        if not cols:
            print("(no result set)")
            return
        widths = [max(len(str(c)), *(len(str(r[i])) for r in rows[:50] or [[""] * len(cols)]))
                  for i, c in enumerate(cols)]
        widths = [min(w, 28) for w in widths]
        line = "  ".join(str(c)[:w].ljust(w) for c, w in zip(cols, widths))
        print("\n" + line)
        print("  ".join("-" * w for w in widths))
        for r in rows[:50]:
            print("  ".join(str(v)[:w].ljust(w) for v, w in zip(r, widths)))
        extra = f"  (showing first 50)" if len(rows) > 50 else ""
        print(f"\n{len(rows)} rows{extra}\n")
    except Exception as e:
        print(f"\n!! {e}\n")


def main():
    if not os.path.exists(DB):
        sys.exit(f"Database not found: {DB}")
    con = duckdb.connect(DB, read_only=True)

    if len(sys.argv) > 2 and sys.argv[1] == "-f":
        run(con, open(sys.argv[2]).read())
        return
    if len(sys.argv) > 1:
        run(con, " ".join(sys.argv[1:]))
        return

    print("RugsUSA practice DB. Type SQL, blank line runs it. Ctrl-C to quit.")
    print("Tables: fct_order_lines, dim_date, dim_customer, dim_product,")
    print("        dim_channel, dim_promotion, order_events, web_events,")
    print("        stg_product, raw_orders\n")
    buf = []
    while True:
        try:
            line = input("sql> " if not buf else "...> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip() == "" and buf:
            run(con, "\n".join(buf))
            buf = []
        elif line.strip():
            buf.append(line)


if __name__ == "__main__":
    main()
