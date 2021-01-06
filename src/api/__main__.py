"""
FastAPI for priority job queue.
"""
import asyncio
import datetime
import uuid

import fastapi
import pydantic


TIMEOUT = 30


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
processing = {}


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


@app.get("/jobs/next")
async def get_next_job():
    """
    Get next job out of the priority queue.

    If the queue is empty, return an empty response.
    """
    try:
        job = queue._queue[0]  # pylint: disable=protected-access
    except IndexError:
        return {}
    try:
        return jobs[job[1]]
    except KeyError:
        # Job has already been removed by its jobId
        return {}


@app.patch("/jobs/next")
async def patch_next_job(status: StatusRequest):
    """
    Patch: pop next job out of the priority queue, put it in the processing list.

    The payload of the incoming request should be {"status": "processing"}.
    """
    if not status.status == "processing":
        raise fastapi.HTTPException(
            status_code=400, detail='Request must have {"status": "processing"}'
        )
    try:
        job = queue.get_nowait()
    except asyncio.QueueEmpty:
        return {}
    job_id = job[1]
    try:
        full_job = jobs[job_id]
    except KeyError:
        # Job has already been removed by its jobId
        return {}
    else:
        processing[job_id] = datetime.datetime.now()
        return full_job


@app.delete("/jobs/next")
async def delete_next_job():
    """
    Delete next job out of the priority queue.  Empty queue will raise an error.
    """
    try:
        job = queue.get_nowait()
    except asyncio.QueueEmpty:
        raise fastapi.HTTPException(  # pylint: disable=raise-missing-from
            status_code=400, detail="Queue is empty, nothing to delete."
        )
    else:
        del jobs[job[1]]


@app.delete("/job/{job_id}")
async def delete_job(job_id):
    """
    Delete given job from the processing jobs.
    """
    try:
        del processing[uuid.UUID(job_id)]
    except KeyError:
        pass
    del jobs[uuid.UUID(job_id)]


async def processing_queue_cleaner():
    """
    Check the processing list for any jobs that have been going for more than
    set timeout number of seconds and return them to the priority queue.
    """
    while True:
        for job_id, timestamp in processing.items():
            if timestamp + datetime.timedelta(0, TIMEOUT) <= datetime.datetime.now():
                # place back in queue
                job = jobs[job_id]
                await queue.put((job.priority, job.jobId))
                del processing[job_id]
            else:
                break
        await asyncio.sleep(0.5)


@app.on_event("startup")
async def startup_event():
    """
    On FastAPI server start-up, register tasks such as the processing queue cleaner.
    """
    asyncio.create_task(processing_queue_cleaner())
