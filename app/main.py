from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import os
import urllib.request
from fastapi.encoders import jsonable_encoder
import base64
import re
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Float, func, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from geoalchemy2.functions import GenericFunction
from sqlalchemy.dialects import sqlite
from sqlalchemy.sql import select
from fastapi.encoders import jsonable_encoder


from models import create_db, load_spatialite

# class ST_TRANSFORM(GenericFunction):
#     name = 'ST_TRANSFORM'
#     type = Geometry

# class ST_GeomFromGeoJSON(GenericFunction):
#     name = 'ST_GeomFromGeoJSON'
#     type = Geometry

engine = create_engine('sqlite:///gistool.db', echo=True)
create_db()

# DBPASSWORD = os.environ.get('DBPASSWORD')
# DBUSER = os.environ.get('DBUSER')
# DBHOST = os.environ.get('DBHOST')
# DBNAME = os.environ.get('DBNAME')

# DATABASE_URL = 'postgresql://' + DBUSER + ':' + DBPASSWORD +  '@' + DBHOST + '/' + DBNAME

# db = create_engine(DATABASE_URL)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/gistool_backend/")
def index():
    return 'index'

Base = declarative_base()
class Polygons(Base):
    __tablename__ = 'polygons'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    geom = Column(Geometry('POLYGON', management=True, srid=4326))

@app.get("/gistool_backend/save_object")
def save_object(data: str):
    listen(engine, 'connect', load_spatialite)
    data = json.loads(data)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()
    name = data['properties']['name']
    try:
        geom = json.dumps(data['geometry'])
    except:
        del data['properties']
        geom = json.dumps(data)
    # polygon = Polygons(name=name, geom=func.ST_Transform(func.GeomFromGeoJSON(json.dumps(data['geometry'])), 4326))
    polygon = Polygons(name=name, geom=func.GeomFromGeoJSON(geom))
    session.add(polygon)
    session.commit()
    conn.close()

@app.get("/gistool_backend/get_all_objects")
def get_all_objects():
    listen(engine, 'connect', load_spatialite)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()
    query = session.query(Polygons.name, Polygons.id, func.ST_AsGeoJSON(Polygons.geom).label('geom'))
    results = []
    # for item in query:
    #     object = {}
    #     print(item)
    #     object['type'] = "FeatureCollection"
    #     object['features'] = item
    #     results.append(object)
    for item in query:
        results.append(item)
    return results