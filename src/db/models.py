from os import getenv

from sqlalchemy import *
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

postgres_db = {
    "drivername": "postgres",
    "username": getenv("DB_USERNAME", "postgres"),
    "password": getenv("DB_PASSWORD"),
    "database": getenv("DB_DB", "discord-employee-health"),
    "host": getenv("DB_HOST", "postgres-master-pg.service.consul"),
    "port": 5432,
}
postgres_url = URL(**postgres_db)
engine = create_engine(postgres_url)
metadata = MetaData()

Base = declarative_base(bind=engine, metadata=metadata)


class EmployeeHours(Base):
    __tablename__ = "employee_hours"

    id = Column(Integer, primary_key=True)
    discordId = Column(String, nullable=False)
    active_start_time = Column(Time(timezone=True), nullable=True)
    active_end_time = Column(Time(timezone=True), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    days = Column(String, nullable=False, default="Sun Mon Tue Wed Thu Fri Sat")

metadata.create_all(engine)


def session_creator() -> Session:
    session = sessionmaker(bind=engine)
    return session()


global_session: Session = session_creator()
