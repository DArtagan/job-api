"""
FastAPI for priority job queue.
"""
import asyncio
import uuid

import fastapi
import pydantic


class Job(pydantic.BaseModel):  # pylint: disable=no-member, too-few-public-methods
    """
    Job model
    """

    jobId: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
    submitterId: int
    priority: int
    name: str
    _status: str = "new"


class StatusRequest(
    pydantic.BaseModel
):  # pylint: disable=no-member, too-few-public-methods
    """
    Request containing a Status.
    """

    status: str


app = fastapi.FastAPI()
queue = asyncio.PriorityQueue()
jobs = {}


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
    jobs[job.jobId] = job
    await queue.put((job.priority, job.jobId))
    return {"jobId": job.jobId}


@app.get("/job/next")
async def get_next_job():
    """
    Get next job out of the priority queue.
    """
    # TODO: This might not be a very concurrency safe approach.
    job = queue._queue[0]
    return jobs[job[1]]


@app.patch("/job/next")
async def patch_next_job(status: StatusRequest):
    """
    Patch: pop next job out of the priority queue.

    The payload of the incoming request should be {"status": "processing"}.
    """
    if not status.status == "processing":
        raise fastapi.HTTPException(
            status_code=400, detail='Request must have {"status": "processing"}'
        )
    job = await queue.get()
    return jobs[job[1]]


@app.delete("/job/next")
async def delete_next_job():
    """
    Delete next job out of the priority queue.
    """
    job = await queue.get()
    del jobs[job[1]]
