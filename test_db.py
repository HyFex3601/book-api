from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv("/Users/yahyazaki/book-api/app/.env")

DATABASE_URL = os.getenv("DATABASE_URL2")
engine = create_engine(DATABASE_URL)

try:
    connection = engine.connect()
    print("✅ Database connection SUCCESS")
    connection.close()
except Exception as e:
    print("❌ Database connection FAILED")
    print(e)