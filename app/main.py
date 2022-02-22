from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import os
import urllib.request
from fastapi.encoders import jsonable_encoder
import base64
import re

from models import create_db
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



@app.get("/")
def index():
    return 'index'
