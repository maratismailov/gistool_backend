from ast import Try
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listen
from geoalchemy2 import Geometry
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select, func

meta = MetaData()

def load_spatialite(dbapi_conn, connection_record):
     dbapi_conn.enable_load_extension(True)
     dbapi_conn.load_extension('/usr/lib/mod_spatialite.so')

def create_db():
    engine = create_engine('sqlite:///gistool.db', echo=True)
    listen(engine, 'connect', load_spatialite)
    conn = engine.connect()
    conn.execute(select([func.InitSpatialMetaData()]))
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()

    Base = declarative_base()

    class Lake(Base):
        __tablename__ = 'lake'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        geom = Column(Geometry('POLYGON', management=True))

    try:
        Lake.__table__.create(engine)
    except:
        print('already exists')
    # meta.create_all(engine)
    lake = Lake(name='Majeur', geom='POLYGON((0 0,1 0,1 1,0 1,0 0))')
    session.add(lake)
    session.commit()
    conn.close()
