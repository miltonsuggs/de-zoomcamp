#!/usr/bin/env python
# coding: utf-8


import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
import pyarrow.parquet as pq
import urllib.request
import click


def run(
    pg_user: str = "root",
    pg_pass: str = "root",
    pg_host: str = "localhost",
    pg_port: int = 5432,
    pg_db: str = "ny_taxi",
    batchsize: int = 100000,
    target_table: str = "yellow_taxi_data",
):
    url = 'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet'
    local_file = 'yellow_tripdata_2021-01.parquet'


    urllib.request.urlretrieve(url, local_file)
    print("Downloaded:", local_file)

    pf = pq.ParquetFile(local_file)

    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')

    pf_iter = pf.iter_batches(batch_size=batchsize)

    first = True

    for batch in tqdm(pf_iter, total=pf.num_row_groups):
        df_chunk = batch.to_pandas()

        if first:
            df_chunk.head(0).to_sql(name=target_table, con=engine, if_exists="replace")
            first = False
            print("Table created")

        df_chunk.to_sql(name=target_table, con=engine, if_exists="append")

        print("Inserted: ", len(df_chunk))


@click.command()
@click.option("--pg-user", default="root", show_default=True, help="Postgres user")
@click.option("--pg-pass", default="root", show_default=True, help="Postgres password")
@click.option("--pg-host", default="localhost", show_default=True, help="Postgres host")
@click.option("--pg-port", default=5432, show_default=True, help="Postgres port")
@click.option("--pg-db", default="ny_taxi", show_default=True, help="Postgres database")
@click.option("--batchsize", default=100000, show_default=True, help="Batch size for parquet iteration")
@click.option("--target-table", default="yellow_taxi_data", show_default=True, help="Target table name")
def main(pg_user, pg_pass, pg_host, pg_port, pg_db, batchsize, target_table):
    run(
        pg_user=pg_user,
        pg_pass=pg_pass,
        pg_host=pg_host,
        pg_port=pg_port,
        pg_db=pg_db,
        batchsize=batchsize,
        target_table=target_table,
    )


if __name__ == "__main__":
    main()



