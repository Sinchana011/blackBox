# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# This connection string is updated with the user you created.
# postgresql://<user>:<password>@<host>/<db_name>
SQLALCHEMY_DATABASE_URL = "postgresql://blackbox_user:password@db/blackbox_guardian_db"

# This part remains the same. It uses the URL above to set up the connection.
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()