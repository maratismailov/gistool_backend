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
# from sqlalchemy.ext.declarative import declarative_base
# from geoalchemy2 import Geometry
# from geoalchemy2.functions import GenericFunction
# from sqlalchemy.dialects import sqlite
# from sqlalchemy.sql import select
from fastapi.encoders import jsonable_encoder


from models import Gnss, Polygons, create_db, load_spatialite

engine = create_engine('sqlite:///gistool.db', echo=True)
create_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "https://gistool.ml", "https://gistool.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return 'index'

# Base = declarative_base()
# class Polygons(Base):
#     __tablename__ = 'polygons'
#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     geom = Column(Geometry('POLYGON', management=True, srid=4326))

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
async def upload_full_output(file: UploadFile, project_name: str = Form(...)):
    out_dir = 'tmp/full_output'
    try:
        shutil.rmtree(out_dir, ignore_errors=True)
        os.remove('tmp/' + file.filename)
    except:
        pass
    try:
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
                            process_summary_file(os.path.join(nested_dir, out_file), project_name)
                elif extension == '.sum':
                    process_summary_file(os.path.join(out_dir, out_file), project_name)
                else:
                    continue
        shutil.rmtree(out_dir, ignore_errors=True)
        os.remove('tmp/' + file.filename)
    except Exception as e:
        print(str(e))
        try:
            shutil.rmtree(out_dir, ignore_errors=True)
        except:
            try:
                os.remove('tmp/' + file.filename)
            except:
                pass
        try:
            os.remove('tmp/' + file.filename)
        except:
            pass

    return {'filename': file.filename}

def parse_dms(dms):
    return float(dms.split()[0]) + float(dms.split()[1])/60 + float(dms.split()[2])/3600

def process_summary_file(file, project_name):
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
            lat_sigma = line.split('    ')[4].split('  ')[0]
            print('decimal lat is ', parse_dms(line.split('    ')[2]))
            continue
        elif 'POS LON' in line:
            print('lon is ', line.split('    ')[2])
            print('decimal lon is ', parse_dms(line.split('    ')[2]))
            lon = parse_dms(line.split('    ')[2])
            lon_sigma = line.split('    ')[4].split('  ')[0]
            continue
        elif 'POS HGT' in line:
            print('hgt is ', line.split()[5])
            hgt = line.split()[5]
            continue

    f.close()

    details = 'lat sigma is ' + lat_sigma + '; lon sigma is ' + lon_sigma + '; height is ' + hgt

    listen(engine, 'connect', load_spatialite)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()
    geom_text = ('POINT({}, {})'.format(lon, lat))
    geom = func.SetSRID(func.MakePoint(lon, lat), 4326)
    geom_kyrg_06 = func.SetSRID(func.MakePoint(lon, lat), 7684)
    gnss = Gnss(project_name = project_name, name=name, details=details, geom=geom)
    print('teiime', func.GeomFromText(geom_text))
    session.add(gnss)
    session.commit()
    conn.close()


@app.get("/get_gnss_points")
def get_gnss_points():
    listen(engine, 'connect', load_spatialite)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()
    query = session.query(func.group_concat(func.json_object('project_name', Gnss.project_name, 'name', Gnss.name, 'details', Gnss.details, 'geojson', func.St_AsGeoJson(Gnss.geom)),',')).group_by(Gnss.project_name).all()
    results = []
    for item in query:
        for subitem in item:
            results.append(subitem)
    # print(query.extracted_text)
    return results
    # 'GROUP_CONCAT(JSON_OBJECT(\'description\', tfard.description , \'deliverable_id\', tfard.deliverable_id, \'result_id\', tfard.result_id) SEPARATOR \'|||\') as deliverables'

@app.get("/recreate_db")
def recreate_db():
    os.remove('gistool.db')
    create_db()

@app.get('/check_for_database')
def check_for_database():
    return os.path.isfile('gistool.db-journal')
