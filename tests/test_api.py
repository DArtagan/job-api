"""
Tests for the api server.
"""
import time
import multiprocessing
import uuid

import requests
import pytest
import uvicorn

from api import __main__


URL = "http://localhost:5000"


def run_server():
    """Run the FastAPI app using Uvicorn."""
    uvicorn.run(__main__.app, port=5000)


@pytest.fixture
def api_server():
    """Before each test, initialize a new FastAPI server in the background."""
    proc = multiprocessing.Process(target=run_server, daemon=True)
    proc.start()
    time.sleep(0.5)  # time for the server to start
    yield None
    proc.kill()


def test_hello_world(api_server):
    """Whether the server turns on."""
    assert requests.get(URL).status_code == 200


def test_submit_job(api_server):
    """Submitted jobs return a jobId."""
    submission = {
        "submitterId": 5,
        "priority": 1,
        "name": "Some string that distinguishes the job",
    }
    response = requests.post(URL + "/jobs", json=submission)
    assert response.status_code == 200
    assert uuid.UUID(response.json()["jobId"], version=4)
