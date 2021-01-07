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
TIMEOUT = 5


def run_server():
    """Run the FastAPI app using Uvicorn."""
    __main__.TIMEOUT = TIMEOUT
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
        {"submitterId": 8, "priority": 2, "name": "Other Two"},
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
    """
    Get next job out of the priority queue.  Should not alter the queue."""
    response = requests.get(URL + "/jobs/next")
    assert response.status_code == 200
    payload = response.json()
    first_job_id = payload["jobId"]
    assert uuid.UUID(first_job_id, version=4)
    assert payload["priority"] == 1
    assert payload["name"] == "One"

    # Queue is unchanged
    response = requests.get(URL + "/jobs/next")
    assert response.status_code == 200
    payload = response.json()
    second_job_id = payload["jobId"]
    assert first_job_id == second_job_id


def test_get_next_job_empty_queue(api_server):
    """Get next job out of the priority queue."""
    response = requests.get(URL + "/jobs/next")
    assert response.status_code == 200
    assert response.json() == {}


def test_delete_next_job(loaded_queue):
    """The next job in the queue can be deleted."""
    response = requests.delete(URL + "/jobs/next")
    assert response.status_code == 200


def test_delete_next_job_empty_queue(api_server):
    """The next job in the queue can be deleted."""
    response = requests.delete(URL + "/jobs/next")
    assert response.status_code == 400


def test_patch_next_job(loaded_queue):
    """Patch: pop next job out of the priority queue."""
    # Get first job
    response = requests.patch(URL + "/jobs/next", json={"status": "processing"})
    assert response.status_code == 200
    payload = response.json()
    first_job_id = payload["jobId"]
    assert uuid.UUID(first_job_id, version=4)
    assert payload["priority"] == 1
    assert payload["name"] == "One"

    # Get second job
    response = requests.patch(URL + "/jobs/next", json={"status": "processing"})
    assert response.status_code == 200
    payload = response.json()
    second_job_id = payload["jobId"]
    assert uuid.UUID(second_job_id, version=4)
    assert first_job_id != second_job_id
    assert payload["priority"] == 2
    assert payload["name"] in ("Two", "Other Two")

    # Get third job
    response = requests.patch(URL + "/jobs/next", json={"status": "processing"})
    assert response.status_code == 200
    payload = response.json()
    third_job_id = payload["jobId"]
    assert uuid.UUID(third_job_id, version=4)
    assert second_job_id != third_job_id
    assert payload["priority"] == 2
    assert payload["name"] in ("Two", "Other Two")


def test_patch_next_job_bad_request_payload(loaded_queue):
    """Patch: with a bad request payload get the next job."""
    response = requests.patch(URL + "/jobs/next", json={"status": "nope"})
    assert response.status_code == 400


def test_delete_job_by_id(api_server):
    """Given an ID, delete the job from the queue."""
    given_uuid = uuid.uuid4()
    submission = {
        "jobId": str(given_uuid),
        "submitterId": 5,
        "priority": 2,
        "name": "Delete me",
    }
    requests.post(URL + "/jobs", json=submission)
    get_response = requests.get(URL + "/jobs/next")
    assert get_response.json()["jobId"] == str(given_uuid)
    delete_response = requests.delete(URL + f"/jobs/{given_uuid}")
    assert delete_response.status_code == 200
    empty_response = requests.get(URL + "/jobs/next")
    assert empty_response.json() == {}


def test_patch_next_job_timeout(loaded_queue):
    """
    After an initial PATCH, jobs are removed from the queue and set aside.  If
    the job is not deleted after 30 seconds, it is returned to the queue.
    """
    first_response = requests.patch(URL + "/jobs/next", json={"status": "processing"})
    first_job_id = first_response.json()["jobId"]
    assert first_response.json()["name"] == "One"

    second_response = requests.get(URL + "/jobs/next")
    second_job_id = second_response.json()["jobId"]
    assert "Two" in second_response.json()["name"]
    assert not first_job_id == second_job_id

    time.sleep(TIMEOUT + 1)

    third_response = requests.get(URL + "/jobs/next")
    third_job_id = third_response.json()["jobId"]
    assert first_job_id == third_job_id


def test_patch_next_job_no_timeout(loaded_queue):
    """
    After an initial PATCH, jobs are removed from the queue and set aside for
    processing.  From there it is also deleted and so, after 30 seconds, it is
    not returned to the queue.
    """
    first_response = requests.patch(URL + "/jobs/next", json={"status": "processing"})
    first_job_id = first_response.json()["jobId"]
    assert first_response.json()["name"] == "One"

    second_response = requests.get(URL + "/jobs/next")
    second_job_id = second_response.json()["jobId"]
    assert "Two" in second_response.json()["name"]
    assert not first_job_id == second_job_id

    delete_response = requests.delete(URL + f"/jobs/{first_job_id}")
    assert delete_response.status_code == 200
    time.sleep(TIMEOUT + 1)

    third_response = requests.get(URL + "/jobs/next")
    third_job_id = third_response.json()["jobId"]
    assert second_job_id == third_job_id
