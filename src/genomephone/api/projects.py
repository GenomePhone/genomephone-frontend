import shutil
from pathlib import Path

import edgedb
import pysam
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, UploadFile, Depends
from kubernetes import client
from confluent_kafka import Producer

from genomephone import edgedb_interface
from genomephone.executor.process import process_project
from genomephone.executor.finish import finish_project



ref_folder = Path("/mnt/references/")

app = FastAPI()


def get_client():
    return edgedb.create_async_client()


def get_k8s_api():
    return client.BatchV1Api()


def get_kafka_producer():
    return Producer({"bootstrap.servers": "kafka:9092"})


def initialize_reference_folder():
    # initialize reference folder
    ref_folder.mkdir(exist_ok=True)


scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(
    "interval", minutes=1,
    args=[get_client(), get_k8s_api(), get_kafka_producer()]
)
async def check_database_for_new(
    client: edgedb.AsyncIOClient, 
    k8s_api: client.BatchV1Api,
    kafka_producer: Producer
):
    for project in await edgedb_interface.get_new_projects(client):
        process_project(kafka_producer, k8s_api, project)
        edgedb_interface.set_project_status(client, project.id, "processing")


@scheduler.scheduled_job("interval", minutes=5, args=[get_client()])
async def check_database_for_done(client: edgedb.AsyncIOClient):
    for project in await edgedb_interface.get_done_projects(client):
        result = finish_project(project)
        edgedb_interface.set_project_result(client, project.id, result)
        edgedb_interface.set_project_status(client, project.id, "done")


@app.on_event("startup")
async def startup():
    scheduler.start()
    initialize_reference_folder()


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()


@app.post("/projects")
async def create_project(
    project_name: str,
    other_files: list[UploadFile],
    db: edgedb.AsyncIOClient = Depends(get_client),
):
    targets = [await f.read() for f in other_files]
    await edgedb_interface.create_project(
        db, name=project_name, targets=targets
    )
    return {"message": "Project created successfully"}


@app.delete("/projects/{project_id}")
async def delete_project(
    project_name: str, db: edgedb.AsyncIOClient = Depends(get_client)
):
    await edgedb_interface.delete_project(db, project_name=project_name)
    return {"message": "Project deleted successfully"}


@app.post("/references")
async def create_reference(
    reference_name: str,
    reference_file: UploadFile,
    db: edgedb.AsyncIOClient = Depends(get_client),
):
    reference_folder = ref_folder / reference_name
    fasta_path = reference_folder / reference_name + ".fasta"
    with fasta_path.open("wb") as f:
        await f.write(await reference_file.read())
    
    pysam.faidx(fasta_path)

    await edgedb_interface.create_reference(db, name=reference_name)
    return {"message": "Reference created successfully"}


@app.delete("/references/{reference_name}")
async def delete_reference(
    reference_name: str,
    db: edgedb.AsyncIOClient = Depends(get_client),
):
    reference_folder = ref_folder / reference_name
    shutil.rmtree(reference_folder)
    await edgedb_interface.delete_reference(db, name=reference_name)
    return {"message": "Reference deleted successfully"}
