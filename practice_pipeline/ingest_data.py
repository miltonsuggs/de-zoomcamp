#!/usr/bin/env python
# coding: utf-8


import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
import pyarrow.parquet as pq
import urllib.request


def run():
    url = 'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet'
    local_file = 'yellow_tripdata_2021-01.parquet'


    urllib.request.urlretrieve(url, local_file)
    print("Downloaded:", local_file)

    pf = pq.ParquetFile(local_file)

    pg_user = "root"
    pg_pass = "root"
    pg_host = "localhost"
    pg_port = 5432
    pg_db = "ny_taxi"

    batchsize = 100000

    target_table = 'yellow_taxi_data'

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


if __name__ == "__main__":
    run()



