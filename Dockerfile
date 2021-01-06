FROM python:alpine

WORKDIR /app

COPY ./src setup.py Pipfile* ./

RUN pip install \
    pipenv \
    uvicorn \
 && pipenv install --system --deploy

COPY . .

CMD uvicorn --host 0.0.0.0 src.api.__main__:app
