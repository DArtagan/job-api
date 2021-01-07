# job-api

Demo: https://job-api.immortalkeep.com/

Docker image: dartagan/job-api


## Installation for development

```
pipenv install --dev
pipenv run pre-commit install
```


## Running locally

`pipenv run uvicorn src.api.__main__:app`


## Testing

`pipenv run pytest`


## Docker (production)

```
docker build --pull -t dartagan/job-api .
docker run --rm -p 8000:8000 dartagan/job-api
```
