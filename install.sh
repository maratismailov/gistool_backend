#!/bin/bash
`python3 -m venv env`
source env/bin/activate
pip install -U pip
pip install fastapi
pip install uvicorn
pip install sqlalchemy
pip install geoalchemy2
pip install python-multipart
pip install aiofiles
pip freeze -> requirements.txt
