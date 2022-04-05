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


# data = '''{"type":"Feature","properties":{"name":"sdfsfsf2"},"geometry":{"type":"Polygon","coordinates":[[[74.449196,42.866622],[74.449196,42.908394],[74.52507,42.908394],[74.52507,42.866622],[74.449196,42.866622]]],"crs":{"type":"name","properties":{"name":"EPSG:4326"}}}}'''
# geom = func.GeomFromGeoJSON(data)



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

def create_db():
    listen(engine, 'connect', load_spatialite)
    conn = engine.connect()
    conn.execute(select([func.InitSpatialMetaData()]))
    # Session = sessionmaker(bind=engine)
    # Session.configure(bind=engine)
    # session = Session()
    try:
        Polygons.__table__.create(engine)
    except:
        print('already exists')
    # polygon = Polygons(name='test2', geom='POLYGON((0 0,1 0,1 1,0 1,0 0))')
    # session.add(polygon)
    # session.commit()
    conn.close()

