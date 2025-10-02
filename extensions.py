from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config
db = SQLAlchemy()
Base = declarative_base()
engine = create_engine(config.DB_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
