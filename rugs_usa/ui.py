#!/usr/bin/env python3
"""
Launch the DuckDB browser UI against the practice database.

    python ui.py

Opens a local web server on port 4213. In a Codespace, VS Code forwards the port
automatically — check the PORTS tab and open the forwarded address.

Leave this running. Closing it shuts the UI down.
"""
import os
import duckdb

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rugsusa_practice.duckdb")

if not os.path.exists(DB):
    raise SystemExit(f"Database not found: {DB}\nRun `python build_db.py` first.")

con = duckdb.connect(DB)
con.sql("CALL start_ui()")

print()
print("  DuckDB UI running.")
print("  Local:      http://localhost:4213")
print("  Codespace:  open the PORTS tab, find 4213, click the globe icon")
print()
print(f"  Database:   {os.path.basename(DB)}")
print("  Tables:     fct_order_lines, dim_date, dim_customer, dim_product,")
print("              dim_channel, dim_promotion, order_events, web_events,")
print("              stg_product, raw_orders")
print()
print("  Ctrl+C to stop.")
print()

try:
    while True:
        input()
except (KeyboardInterrupt, EOFError):
    print("\nStopped.")
