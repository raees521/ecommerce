import mysql.connector
import sqlite3
import pandas as pd

# 1. Connect to your local MySQL database
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="raees",
    database="ecommerce_analytics"
)

# 2. Automatically create 'ecommerce.db' in your project folder
sqlite_conn = sqlite3.connect("ecommerce.db")

# 3. Export all your tables over to SQLite
tables = ["orders", "order_items", "products"]

for table in tables:
    df = pd.read_sql(f"SELECT * FROM {table}", mysql_conn)
    df.to_sql(table, sqlite_conn, if_exists="replace", index=False)
    print(f"✅ Exported table '{table}' to SQLite!")

mysql_conn.close()
sqlite_conn.close()
