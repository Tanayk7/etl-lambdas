from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, CHAR
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Vendor(Base):
    __tablename__ = 'vendors'
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, unique=True, nullable=False)

class Trip(Base):
    __tablename__ = 'trips'
    id = Column(String, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'))
    pickup_datetime = Column(DateTime)
    dropoff_datetime = Column(DateTime)
    passenger_count = Column(Integer)
    pickup_longitude = Column(Float)
    pickup_latitude = Column(Float)
    dropoff_longitude = Column(Float)
    dropoff_latitude = Column(Float)
    store_and_fwd_flag = Column(CHAR(1))
    trip_duration = Column(Integer)
    trip_distance = Column(Float)