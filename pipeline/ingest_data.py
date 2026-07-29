#!/usr/bin/env python
# coding: utf-8


import pandas as pd
import click
from sqlalchemy import create_engine
from tqdm.auto import tqdm


dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]


@click.command()
@click.option("--pg-user", default="root", show_default=True, help="Postgres username.")
@click.option("--pg-pass", default="root", show_default=True, help="Postgres password.")
@click.option("--pg-host", default="localhost", show_default=True, help="Postgres host.")
@click.option("--pg-port", type=int, default=5432, show_default=True, help="Postgres port.")
@click.option("--pg-db", default="ny_taxi", show_default=True, help="Postgres database name.")
@click.option("--year", type=int, default=2021, show_default=True, help="Taxi data year to ingest.")
@click.option("--month", type=int, default=1, show_default=True, help="Taxi data month to ingest.")
@click.option("--target-table", default="yellow_taxi_data", show_default=True, help="Destination table name.")
@click.option("--chunksize", type=int, default=100000, show_default=True, help="Number of rows per chunk.")
def main(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, target_table, chunksize):
    run(
        pg_user=pg_user,
        pg_pass=pg_pass,
        pg_host=pg_host,
        pg_port=pg_port,
        pg_db=pg_db,
        year=year,
        month=month,
        target_table=target_table,
        chunksize=chunksize,
    )


def run(pg_user="root", pg_pass="root", pg_host="localhost", pg_port=5432, pg_db="ny_taxi", year=2021, month=1, target_table="yellow_taxi_data", chunksize=100000):
    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow'
    url = f"{prefix}/yellow_tripdata_{year}-{month:02d}.csv.gz"

    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')

    df_iter = pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize
    )

    first = True

    for df_chunk in tqdm(df_iter):

        if first:
            # Create table schema (no data)
            df_chunk.head(0).to_sql(
                name=target_table,
                con=engine,
                if_exists="replace"
            )
            first = False
            print("Table created")

        # Insert chunk
        df_chunk.to_sql(
            name=target_table,
            con=engine,
            if_exists="append"
        )

        print("Inserted:", len(df_chunk))


if __name__ == "__main__":
    main()