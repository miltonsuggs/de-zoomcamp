import duckdb, random, json, os, datetime as dt

random.seed(42)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rugsusa_practice.duckdb")
if os.path.exists(DB):
    os.remove(DB)
con = duckdb.connect(DB)

# ---------- DIM_DATE ----------
start = dt.date(2024, 1, 1)
end = dt.date(2025, 12, 31)
dates = []
d = start
while d <= end:
    dates.append((int(d.strftime("%Y%m%d")), d, d.month, (d.month - 1)//3 + 1,
                  d.year, d.weekday() >= 5, d.strftime("%B")))
    d += dt.timedelta(days=1)
con.execute("""CREATE TABLE dim_date(date_key INT PRIMARY KEY, full_date DATE, month INT,
               quarter INT, year INT, is_weekend BOOLEAN, month_name VARCHAR)""")
con.executemany("INSERT INTO dim_date VALUES (?,?,?,?,?,?,?)", dates)

# ---------- DIM_PRODUCT (SCD Type 2) ----------
collections = ["Bohemian", "Modern Loft", "Persian Classic", "Coastal", "Farmhouse", "Moroccan Shag"]
materials = ["Wool", "Polypropylene", "Jute", "Cotton", "Viscose", "Silk Blend"]
sizes = ["3x5", "5x8", "8x10", "9x12", "2x7 Runner", "Round 6ft"]
colors = ["Ivory", "Charcoal", "Navy", "Rust", "Sage", "Multi", None]  # None -> NULL practice
tiers = ["Budget", "Mid", "Premium", "Luxury"]

prod_rows, pkey = [], 1
for pid in range(1, 121):
    product_id = f"RUG-{pid:04d}"
    coll, mat = random.choice(collections), random.choice(materials)
    size, col = random.choice(sizes), random.choice(colors)
    tier = random.choice(tiers)
    cost = round(random.uniform(25, 400), 2)
    # ~20% of products get an SCD2 version change (price tier changed mid-2025)
    if random.random() < 0.20:
        prod_rows.append((pkey, product_id, coll, mat, size, col, tier, cost,
                          dt.date(2024,1,1), dt.date(2025,6,30), False)); pkey += 1
        new_tier = random.choice([t for t in tiers if t != tier])
        prod_rows.append((pkey, product_id, coll, mat, size, col, new_tier, round(cost*1.15,2),
                          dt.date(2025,7,1), dt.date(9999,12,31), True)); pkey += 1
    else:
        prod_rows.append((pkey, product_id, coll, mat, size, col, tier, cost,
                          dt.date(2024,1,1), dt.date(9999,12,31), True)); pkey += 1

con.execute("""CREATE TABLE dim_product(product_key INT PRIMARY KEY, product_id VARCHAR,
    collection VARCHAR, material VARCHAR, size VARCHAR, color VARCHAR, price_tier VARCHAR,
    cost_amount DECIMAL(10,2), effective_date DATE, expiration_date DATE, is_current BOOLEAN)""")
con.executemany("INSERT INTO dim_product VALUES (?,?,?,?,?,?,?,?,?,?,?)", prod_rows)

# ---------- DIM_CUSTOMER ----------
states = ["NY","CA","TX","FL","IL","PA","OH","GA","NC","NJ"]
segments = ["New", "Returning", "VIP", None]
acq = ["Paid Search", "Organic", "Email", "Social", "Affiliate"]
cust_rows = []
for c in range(1, 861):  # 801-860 deliberately have no orders (anti-join drill)
    cust_rows.append((c, f"CUST-{c:05d}", random.choice(states), random.choice(segments),
                      random.choice(acq), start + dt.timedelta(days=random.randint(0, 600))))
con.execute("""CREATE TABLE dim_customer(customer_key INT PRIMARY KEY, customer_id VARCHAR,
    state VARCHAR, segment VARCHAR, acq_channel VARCHAR, first_order_date DATE)""")
con.executemany("INSERT INTO dim_customer VALUES (?,?,?,?,?,?)", cust_rows)

# ---------- DIM_CHANNEL ----------
chan_rows = [(1,"Website","Direct","Desktop"),(2,"Website","Direct","Mobile"),
             (3,"Amazon","Marketplace","Mobile"),(4,"Wayfair","Marketplace","Desktop"),
             (5,"Phone Order","Direct","N/A")]
con.execute("""CREATE TABLE dim_channel(channel_key INT PRIMARY KEY, channel_name VARCHAR,
    marketplace VARCHAR, device_type VARCHAR)""")
con.executemany("INSERT INTO dim_channel VALUES (?,?,?,?)", chan_rows)

# ---------- DIM_PROMOTION ----------
promo_rows = [(1,"No Promotion","None",0.0),(2,"Spring Sale","Seasonal",15.0),
              (3,"Black Friday","Seasonal",30.0),(4,"Email 10 Off","Email",10.0),
              (5,"Clearance","Clearance",40.0),(6,"New Customer","Acquisition",20.0),
              (7,"Summer Rug Event","Seasonal",25.0),(8,"Loyalty Reward","Retention",12.0)]
con.execute("""CREATE TABLE dim_promotion(promotion_key INT PRIMARY KEY, promo_name VARCHAR,
    promo_type VARCHAR, discount_pct DECIMAL(5,2))""")
con.executemany("INSERT INTO dim_promotion VALUES (?,?,?,?)", promo_rows)

# ---------- FCT_ORDER_LINES ----------
statuses = ["completed","completed","completed","completed","returned","cancelled"]
cats = {c: c for c in collections}
fact_rows = []
order_no = 100000
# deliberately skip some dates entirely -> date-spine drill has real gaps
skip_days = set(random.sample(range(0, 730), 45))
for day_offset in range(0, 730):
    if day_offset in skip_days:
        continue
    dd = start + dt.timedelta(days=day_offset)
    for _ in range(random.randint(8, 40)):
        order_no += 1
        oid = f"ORD-{order_no}"
        cust = random.randint(1, 800)
        chan = random.choice([1,1,2,2,2,3,3,4,5])
        promo = random.choice([1,1,1,1,2,3,4,5,6,7,8])
        for _line in range(random.randint(1, 3)):
            p = random.choice(prod_rows)
            pk, cost = p[0], float(p[7])
            qty = random.randint(1, 3)
            price = round(cost * random.uniform(2.0, 3.4), 2)
            disc = round(price * qty * (float(promo_rows[promo-1][3]) / 100), 2)
            net = round(price * qty - disc, 2)
            ship = round(random.choice([0.0, 0.0, 9.99, 19.99, 49.99]), 2)
            fact_rows.append((int(dd.strftime("%Y%m%d")), cust, pk, chan, promo, oid,
                              qty, price, disc, net, round(cost*qty,2), ship,
                              random.choice(statuses)))

con.execute("""CREATE TABLE fct_order_lines(date_key INT, customer_key INT, product_key INT,
    channel_key INT, promotion_key INT, order_id VARCHAR, quantity INT,
    unit_price DECIMAL(10,2), discount_amount DECIMAL(10,2), net_revenue DECIMAL(10,2),
    cost_amount DECIMAL(10,2), shipping_amount DECIMAL(10,2), status VARCHAR)""")
con.executemany("INSERT INTO fct_order_lines VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", fact_rows)

# ---------- ORDER_EVENTS (dedup drill: many rows per order) ----------
ev_rows = []
sample_orders = random.sample([r[5] for r in fact_rows], 4000)
for oid in set(sample_orders):
    base = dt.datetime(2025, random.randint(1,12), random.randint(1,28), random.randint(0,23))
    seq = ["placed","paid","shipped","delivered"]
    for i, s in enumerate(seq[:random.randint(1,4)]):
        ev_rows.append((oid, s, base + dt.timedelta(days=i, hours=random.randint(0,10))))
    if random.random() < 0.15:  # true duplicates
        ev_rows.append((oid, "placed", base))
con.execute("CREATE TABLE order_events(order_id VARCHAR, status VARCHAR, event_time TIMESTAMP)")
con.executemany("INSERT INTO order_events VALUES (?,?,?)", ev_rows)

# ---------- WEB_EVENTS (sessionization drill) ----------
web_rows = []
for c in random.sample(range(1, 801), 300):
    t = dt.datetime(2025, random.randint(1,12), random.randint(1,28), random.randint(8,20))
    for _ in range(random.randint(5, 30)):
        web_rows.append((c, t, random.choice(["view_pdp","search","add_to_cart","checkout","home"])))
        gap = random.choice([1,2,3,5,8,45,90,120])  # some gaps > 30 min -> new session
        t += dt.timedelta(minutes=gap)
con.execute("CREATE TABLE web_events(customer_key INT, event_time TIMESTAMP, event_type VARCHAR)")
con.executemany("INSERT INTO web_events VALUES (?,?,?)", web_rows)

# ---------- STG_PRODUCT (MERGE / SCD2 drill) ----------
stg = []
for p in random.sample(prod_rows, 40):
    stg.append((p[1], p[2], p[3], p[4], p[5],
                random.choice(tiers), round(float(p[7])*random.uniform(0.9,1.2),2), dt.date(2026,1,15)))
for n in range(121, 131):  # brand new products
    stg.append((f"RUG-{n:04d}", random.choice(collections), random.choice(materials),
                random.choice(sizes), random.choice(colors), random.choice(tiers),
                round(random.uniform(25,400),2), dt.date(2026,1,15)))
con.execute("""CREATE TABLE stg_product(product_id VARCHAR, collection VARCHAR, material VARCHAR,
    size VARCHAR, color VARCHAR, price_tier VARCHAR, cost_amount DECIMAL(10,2), updated_at DATE)""")
con.executemany("INSERT INTO stg_product VALUES (?,?,?,?,?,?,?,?)", stg)

# ---------- RAW_ORDERS (JSON flatten drill) ----------
raw = []
for i in range(500):
    payload = {"order_id": f"API-{i:05d}",
               "customer": {"id": f"CUST-{random.randint(1,800):05d}", "state": random.choice(states)},
               "line_items": [{"sku": f"RUG-{random.randint(1,120):04d}",
                               "qty": random.randint(1,3),
                               "price": round(random.uniform(60,900),2)}
                              for _ in range(random.randint(1,4))]}
    raw.append((f"API-{i:05d}", json.dumps(payload)))
con.execute("CREATE TABLE raw_orders(order_id VARCHAR, payload JSON)")
con.executemany("INSERT INTO raw_orders VALUES (?,?)", raw)

# ---------- Verify ----------
for t in ["dim_date","dim_product","dim_customer","dim_channel","dim_promotion",
          "fct_order_lines","order_events","web_events","stg_product","raw_orders"]:
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t:20s} {n:>8,} rows")
con.close()
print("\nDB written to", DB)
