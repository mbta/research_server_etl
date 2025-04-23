import os
from typing import List

import boto3

from research_etl.utils.util_logging import ProcessLogger


def get_s3_client() -> boto3.client:
    """Thin function needed for stubbing tests"""
    aws_profile = os.getenv("AWS_PROFILE", None)

    if aws_profile is not None:
        return boto3.Session(profile_name=aws_profile).client("s3")

    return boto3.client("s3")


def download_file(object_path: str, file_name: str) -> bool:
    """
    Download an S3 object to a local file
    will overwrite local file, if exists

    :param object_path: S3 object path to download from (including bucket)
    :param file_name: local file path to save object to

    :return: True if file was downloaded, else False
    """
    download_log = ProcessLogger(
        "s3_download_file",
        file_name=file_name,
        object_path=object_path,
    )

    try:
        if os.path.exists(file_name):
            os.remove(file_name)

        object_path = object_path.replace("s3://", "")
        bucket, object_name = object_path.split("/", 1)

        s3_client = get_s3_client()

        s3_client.download_file(bucket, object_name, file_name)

        download_log.log_complete()

        return True

    except Exception as exception:
        download_log.log_failure(exception=exception)
        return False


def file_list_from_s3(bucket_name: str, file_prefix: str, max_list_size: int = 250_000) -> List[str]:
    """
    provide list of s3 objects based on bucket_name and file_prefix

    :param bucket_name: the name of the bucket to look inside of
    :param file_prefix: prefix for files to generate

    :return list of s3 filepaths formated as s3://bucket_name/object_name
    """
    process_logger = ProcessLogger("file_list_from_s3", bucket_name=bucket_name, file_prefix=file_prefix)

    try:
        s3_client = get_s3_client()
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix=file_prefix)

        filepaths = []
        for page in pages:
            if page["KeyCount"] == 0:
                continue
            for obj in page["Contents"]:
                if obj["Size"] == 0:
                    continue
                filepaths.append(os.path.join("s3://", bucket_name, obj["Key"]))

            if len(filepaths) > max_list_size:
                break

        process_logger.add_metadata(list_size=len(filepaths))
        process_logger.log_complete()
        return filepaths

    except Exception as exception:
        process_logger.log_failure(exception)
        return []


def delete_object(del_obj: str) -> bool:
    """
    delete s3 object

    :param del_obj - expected as 's3://my_bucket/object' or 'my_bucket/object'

    :return: True if file success, else False
    """
    try:
        process_logger = ProcessLogger("delete_s3_object", del_obj=del_obj)

        s3_client = get_s3_client()

        # trim off leading s3://
        del_obj = del_obj.replace("s3://", "")

        # split into bucket and object name
        bucket, obj = del_obj.split("/", 1)

        # delete the source object
        _ = s3_client.delete_object(
            Bucket=bucket,
            Key=obj,
        )

        process_logger.log_complete()
        return True

    except Exception as error:
        process_logger.log_failure(error)
        return False


def rename_s3_object(source_obj: str, dest_obj: str) -> bool:
    """
    rename source_obj to dest_obj as copy and delete operation

    :param source_obj - expected as 's3://my_bucket/object' or 'my_bucket/object'
    :param dest_obj - expected as 's3://my_bucket/object' or 'my_bucket/object'

    :return: True if file success, else False
    """
    try:
        process_logger = ProcessLogger("rename_s3_object", source_obj=source_obj, dest_obj=dest_obj)

        s3_client = get_s3_client()

        # trim off leading s3://
        source_obj = source_obj.replace("s3://", "")
        dest_obj = dest_obj.replace("s3://", "")

        # split into bucket and object name
        to_bucket, to_obj = dest_obj.split("/", 1)

        # copy object
        _ = s3_client.copy_object(
            Bucket=to_bucket,
            CopySource=source_obj,
            Key=to_obj,
        )

        if not delete_object(source_obj):
            raise FileExistsError(f"failed to delete {source_obj}")

        process_logger.log_complete()
        return True

    except Exception as error:
        process_logger.log_failure(error)
        return False


def running_in_aws() -> bool:
    """
    return True if running on aws, else False
    """
    return bool(os.getenv("AWS_DEFAULT_REGION"))


def check_for_parallel_tasks() -> None:
    """
    Check that that this task is not already running on ECS
    """
    if not running_in_aws():
        return

    process_logger = ProcessLogger("check_for_tasks")

    client = boto3.client("ecs")
    ecs_cluster = os.environ["ECS_CLUSTER"]
    ecs_task_group = os.environ["ECS_TASK_GROUP"]

    # get all of the tasks running on the cluster
    task_arns = client.list_tasks(cluster=ecs_cluster)["taskArns"]

    # if tasks are running on the cluster, get their descriptions and check to
    # count matches the ecs task group.
    match_count = 0
    if task_arns:
        running_tasks = client.describe_tasks(cluster=ecs_cluster, tasks=task_arns)["tasks"]

        for task in running_tasks:
            if ecs_task_group == task["group"]:
                match_count += 1

    # if the group matches, raise an exception that will terminate the process
    if match_count > 1:
        exception = SystemError(f"Multiple {ecs_cluster} ECS Tasks Running")
        process_logger.log_failure(exception)
        raise exception

    process_logger.log_complete()
