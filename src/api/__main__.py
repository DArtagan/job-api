"""
FastAPI for priority job queue.
"""
import asyncio
import uuid

from fastapi import FastAPI
from pydantic import BaseModel  # pylint: disable=no-name-in-module


class Job(BaseModel):  # pylint: disable=too-few-public-methods
    """
    Job model
    """

    submitterId: int
    priority: int
    name: str


app = FastAPI()
queue = asyncio.PriorityQueue()
queue = asyncio.Queue()


@app.get("/")
async def root():
    """
    Simple welcome message for GETs to the root.
    """
    return {"message": "Hello World"}


@app.post("/jobs")
async def submit_job(job: Job):
    """
    Add job to the priority queue.
    """
    job_id = uuid.uuid4()
    queue.put((job.priority, (job_id, job)))
    return {"jobId": job_id}
