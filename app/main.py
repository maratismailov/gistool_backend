import shutil
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import os
import urllib.request
import zipfile
import aiofiles
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


from models import Gnss, create_db, load_spatialite

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
    allow_origins=["http://localhost:5000", "https://gistool.ml"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def index():
    return 'index'

Base = declarative_base()
class Polygons(Base):
    __tablename__ = 'polygons'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    geom = Column(Geometry('POLYGON', management=True, srid=4326))

@app.get("/save_object")
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

@app.get("/get_all_objects")
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

@app.post("/upload_full_output")
async def upload_full_output(file: UploadFile):
    out_dir = 'tmp/full_output'
    if 'zip' not in file.filename:
        return 'wrong filetype'
    async with aiofiles.open('tmp/' + file.filename, 'wb') as out_file:
        content = await file.read()  # async read
        await out_file.write(content)  # async write
        os.mkdir(out_dir)
        with zipfile.ZipFile('tmp/' + file.filename, 'r') as zip_ref:
            zip_ref.extractall(out_dir)
        for out_file in  os.listdir(out_dir):
            filename, extension = os.path.splitext(out_file)
            if extension == '.zip' and filename != 'errors':
                nested_dir = out_dir + '/' + out_file.replace('.zip', '')
                os.mkdir(nested_dir)
                with zipfile.ZipFile(out_dir + '/' + out_file, 'r') as zip_ref:
                    zip_ref.extractall(nested_dir)
                for out_file in os.listdir(nested_dir):
                    filename, extension = os.path.splitext(out_file)
                    if extension == '.sum':
                        process_summary_file(os.path.join(nested_dir, out_file))
            elif extension == '.sum':
                process_summary_file(os.path.join(out_dir, out_file))
            else:
                continue
        shutil.rmtree(out_dir, ignore_errors=True)
        os.remove('tmp/' + file.filename)

    return {'filename': file.filename}

def parse_dms(dms):
    return float(dms.split()[0]) + float(dms.split()[1])/60 + float(dms.split()[2])/3600

def process_summary_file(file):
    with open(file) as f:
        lines = f.readlines()
    for line in lines:
        if 'MKR' in line:
            print('point is ', line.split()[1])
            name = line.split()[1]
            continue
        elif 'POS LAT' in line:
            print('lat is ', line.split('    ')[2])
            lat = parse_dms(line.split('    ')[2])
            lat_sigma = line.split('    ')[4]
            print('decimal lat is ', parse_dms(line.split('    ')[2]))
            continue
        elif 'POS LON' in line:
            print('lon is ', line.split('    ')[2])
            print('decimal lon is ', parse_dms(line.split('    ')[2]))
            lon = parse_dms(line.split('    ')[2])
            lon_sigma = line.split('    ')[4]
            continue
        elif 'POS HGT' in line:
            print('hgt is ', line.split()[5])
            hgt = line.split()[5]
            continue

    f.close()

    details = 'lat sigma is ' + lat_sigma + ', lon sigma is ' + lon_sigma + ', height is ' + hgt

    listen(engine, 'connect', load_spatialite)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()
    geom_text = ('POINT({}, {})'.format(lon, lat))
    print(geom_text)
    geom = func.GeomFromText(geom_text, 4326)
    # geom = func.SetSRID(func.MakePoint(lon, lat), 4326);
    geom = func.SetSRID(func.MakePoint(lon, lat), 4326)

    gnss = Gnss(name=name, details=details, geom=geom)
    # polygon = Polygons(name=name, geom=func.GeomFromGeoJSON(geom))

    print('teiime', func.GeomFromText(geom_text))
    session.add(gnss)
    session.commit()
    conn.close()



    # the_geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326);




    # POS LAT IGb14 22:132:44430    42 50 20.41745    42 50 20.35770    -1.8437     0.0080  1.0000

    # 42 50 20.35770


@app.get("/get_gnss_points")
def get_gnss_points():
    listen(engine, 'connect', load_spatialite)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()
    query = session.query(Gnss.name, Gnss.details, func.ST_AsGeoJSON(Gnss.geom).label('geom'))
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