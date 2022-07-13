# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import datetime
import time
import uuid
import msrest
import pprint
from azure.iot.hub import IoTHubJobManager
from azure.iot.hub.models import JobRequest, Twin, TwinProperties


iothub_connection_str = os.getenv("IOTHUB_CONNECTION_STRING")


def create_twin_update_job_request():
    job = JobRequest()
    job.job_id = "twinjob-" + str(uuid.uuid4())
    job.type = "scheduleUpdateTwin"
    job.start_time = datetime.datetime.utcnow().isoformat()
    job.update_twin = Twin(etag="*", properties=TwinProperties(desired={"temperature": 98.6}))
    job.query_condition = "*"
    return job


def print_job_response(title, response):
    print()
    print(title)
    pprint.pprint(response.as_dict())


try:
    # Create IoTHubJobManager
    iothub_job_manager = IoTHubJobManager.from_connection_string(iothub_connection_str)

    # Create  job
    job_request = create_twin_update_job_request()
    new_job_response = iothub_job_manager.create_scheduled_job(job_request.job_id, job_request)
    print_job_response("Create job response: ", new_job_response)

    # Get job
    while True:
        get_job_response = iothub_job_manager.get_scheduled_job(job_request.job_id)
        print_job_response("Get job response: ", get_job_response)
        if get_job_response.status == "completed":
            break
        time.sleep(5)

except msrest.exceptions.HttpOperationError as ex:
    print("HttpOperationError error {0}".format(ex.response.text))
except Exception as ex:
    print("Unexpected error {0}".format(ex))
except KeyboardInterrupt:
    print("{} stopped".format(__file__))
finally:
    print("{} finished".format(__file__))
