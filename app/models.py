from ast import Try
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listen
from geoalchemy2 import Geometry
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select, func

meta = MetaData()
engine = create_engine('sqlite:///gistool.db', echo=True)
Base = declarative_base()


def load_spatialite(dbapi_conn, connection_record):
    dbapi_conn.enable_load_extension(True)
    try:
        dbapi_conn.load_extension('/usr/lib/mod_spatialite.so')
    except:
        try:
            dbapi_conn.load_extension('/usr/lib/aarch64-linux-gnu/mod_spatialite.so')
        except:
            dbapi_conn.load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite.so')
    

class Polygons(Base):
    __tablename__ = 'polygons'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    geom = Column(Geometry('POLYGON', management=True, srid=4326))

class Gnss(Base):
    __tablename__ = 'gnss_points'
    id = Column(Integer, primary_key=True)
    project_name = Column(String)
    name = Column(String)
    geom = Column(Geometry('POINT', management=True, srid=4326))
    details = Column(String)

def create_db():
    listen(engine, 'connect', load_spatialite)
    conn = engine.connect()
    conn.execute(select([func.InitSpatialMetaData()]))
    try:
        Polygons.__table__.create(engine)
        Gnss.__table__.create(engine)
    except:
        print('already exists')
    conn.close()

