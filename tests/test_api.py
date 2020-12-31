import time
import threading

import requests
import pytest
import uvicorn

from api import __main__


URL = "http://localhost:5000"


@pytest.fixture
def api_server():
    app = __main__.app
    proc = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "127.0.0.1", "port": 5000, "log_level": "info"},
        daemon=True,
    )
    proc.start()
    time.sleep(0.1)  # time for the server to start


def test_hello_world(api_server):
    """
    Test whether the server turns on.
    """
    assert requests.get(URL).status_code == 200
