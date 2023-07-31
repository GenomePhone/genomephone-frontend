from pathlib import Path

import pysam
from confluent_kafka import Producer
from kubernetes import client

from genomephone.edgedb_interface import create_chunk


def create_k8s_job(api_instance, project_id, num_chunks):
    # Define the job
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(
            name=f"genomephone-{project_id}"[:63],
            namespace="default"
        ),
        spec=client.V1JobSpec(
            parallelism=num_chunks,
            template=client.V1PodTemplateSpec(
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="varscan-worker",
                            image="ghcr.io/genomephone/genomephone-worker-varscan:latest",
                            env=[
                                client.V1EnvVar(
                                    name="PROJECT_ID",
                                    value=project_id
                                )
                            ]
                        )
                    ],
                    restart_policy="Never",
                )
            )
        )
    )

    # Create the job
    api_instance.create_namespaced_job(
        namespace="default",
        body=job
    )


def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')


def publish_message(producer: Producer, topic, key, value):
    # Produce message to Kafka
    producer.produce(topic, key=key, value=value, callback=delivery_report)


def preprocess_target(genome):
    # save the genome data to a bam file for indexing and sorting
    genome_bam_path = Path(f"{genome.id}.bam")
    with pysam.AlignmentFile(genome_bam_path, "wb") as bam_file:
        bam_file.write(genome.data)

    # sort and index the bam file
    pysam.sort("-o", genome_bam_path, genome_bam_path)
    pysam.index(genome_bam_path)

    # split the genome data into chunks
    with pysam.AlignmentFile(genome_bam_path, "rb") as bam_file:
        for ref in bam_file.references:
            for read in bam_file.fetch(ref):
                yield read

    # delete the bam file
    genome_bam_path.unlink()


def make_mpileup(chunk, reference_file):
    result = ""
    with pysam.AlignmentFile(chunk, "rb") as bam_file:
        for pileupcolumn in bam_file.pileup(fastafile=reference_file):
            result += "\t".join(str(x) for x in [pileupcolumn.reference_name,
                                                 pileupcolumn.reference_pos,
                                                 pileupcolumn.nsegments,
                                                 pileupcolumn.get_query_sequences()]) + "\n"
    return result


def process_project(kafka_producer, k8s_instance, project, references_path):
    # split each target into chunks, store in db, and publish chunk ids to kafka
    num_chunks = 0
    for target in project.targets:
        for chunk in preprocess_target(target.data):
            mpileup = make_mpileup(chunk, references_path / project.reference.name)
            chunk_id = create_chunk(target, mpileup)
            publish_message(kafka_producer, project.id, "chunk_id", chunk_id)
            num_chunks += 1

    kafka_producer.flush()

    # create a k8s job to process the chunks
    create_k8s_job(k8s_instance, project.id, num_chunks)
