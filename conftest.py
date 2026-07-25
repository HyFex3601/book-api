from dotenv import load_dotenv

load_dotenv(".env.test")

from app.database import Base
from app.database import engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)