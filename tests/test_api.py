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


@pytest.fixture
def loaded_queue(api_server):
    """Preload up the priority queue with several entries."""
    submissions = [
        {"submitterId": 5, "priority": 2, "name": "Two"},
        {"submitterId": 7, "priority": 1, "name": "One"},
        {"submitterId": 7, "priority": 3, "name": "Three"},
    ]
    for submission in submissions:
        requests.post(URL + "/jobs", json=submission)


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


def test_get_next_job(loaded_queue):
    """Get next job out of the priority queue."""
    response = requests.get(URL + "/job/next")
    assert response.status_code == 200
    payload = response.json()
    assert uuid.UUID(payload["jobId"], version=4)
    assert payload["priority"] == 1
    assert payload["name"] == "One"


def test_delete_next_job(loaded_queue):
    """The next job in the queue can be deleted."""
    response = requests.delete(URL + "/job/next")
    assert response.status_code == 200


def test_patch_next_job(loaded_queue):
    """Patch: pop next job out of the priority queue."""
    response = requests.patch(URL + "/job/next", json={"status": "processing"})
    assert response.status_code == 200
    payload = response.json()
    assert uuid.UUID(payload["jobId"], version=4)
    assert payload["priority"] == 1
    assert payload["name"] == "One"


def test_patch_next_job_bad_request_payload(loaded_queue):
    """Patch: with a bad request payload get the next job."""
    response = requests.patch(URL + "/job/next", json={"status": "nope"})
    assert response.status_code == 400
