FROM python:3.9

WORKDIR /code

COPY ./install.sh /code/install.sh

RUN apt update && apt install -y libsqlite3-mod-spatialite && ./install.sh

COPY ./app /code/app

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
CMD . /code/env/bin/activate && cd /code/app && exec uvicorn main:app --host 0.0.0.0 --port 80