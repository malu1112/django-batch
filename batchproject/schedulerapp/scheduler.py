import json
import time
import atexit
import logging
import random
import socket

from datetime import datetime
from django.utils import timezone

from schedulerapp.models import BatchJob
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def get_latest_job(job_id):
    """
    Get the specific job object
    :param job_id:
    :return:
    """
    try:
        job = BatchJob.objects.get(job_id=job_id)
        return job
    except Exception as e:
        logger.error(f'Exception get_latest_job: {e}')
        return None


def do_job_update(job_id, job_status, job_content):
    """
    Update the job status and job content
    :param job_id:
    :param job_status:
    :param job_content:
    :return:
    """
    try:
        job = get_latest_job(job_id)
        job_content = json.dumps(job_content)
        job.job_status = job_status
        job.job_content = job_content
        job.last_updated_ts = timezone.now()
        job.save()
        return True
    except Exception as e:
        logger.error(f'Exception in do_job_update: {e}')
        return False


def do_batch_preliminary_check(job_id):
    """
    This is where actual batch function works
    1. Identify the batch is enabled
    2. Make sure batch is not running already
    3. Make sure batch is not overlapping with same batch in cluster servers
    :return:
    """
    try:
        job = get_latest_job(job_id=job_id)
        # Make sure job is enabled
        if not job.job_enabled:
            logger.warning(f'Job [{job_id}]=[{job.job_name}] is in disabled state, cannot run now')
            return False
        # Make sure job is not already RUNNING
        elif job.job_status == 1:
            logger.warning(f'Job [{job_id}]=[{job.job_name}] is already running, cannot run now')
            return False
        # Do a random sleep between 5 and 20 seconds.
        # This will take care of overlapping the jobs between multiple clusters.
        for i in range(1, 4):
            sleep_time = random.randint(5, 20)
            logger.info(f'Job [{job.job_name}] Host [{socket.gethostname()}] sleeping {sleep_time} seconds for loop {i}')
            time.sleep(sleep_time)
        job = get_latest_job(job_id=job_id)
        # Validate the job last completed timestamp is not less than a five minutes ago
        last_updated_ts = job.last_updated_ts
        current_ts = timezone.now()
        # # To avoid TypeError
        # current_ts = current_ts.replace()
        logger.info(f'Job [{job.job_name}] Last Updated TS and Current TS: [{last_updated_ts}]=[{current_ts}]')
        total_seconds = (current_ts - last_updated_ts).total_seconds()
        logger.info(f'Job [{job.job_name}] total_seconds: {total_seconds} and job_run_lag_check: {job.job_run_lag_check}')
        if int(total_seconds) <= job.job_run_lag_check: # last Execution was not less than X minutes ago
            return False
    except Exception as e:
        logger.error(f'Exception in do_batch_preliminary_check: {e}')
        return False
    return True


def batch_job_worker(job_id):
    """
    Single job worker to run all the batch jobs
    :param job_id:
    :return:
    """
    logger.info('Entered into batch_job_worker')
    job = get_latest_job(job_id=job_id)
    logger.info(f'Going to run a job: [{job_id}]=[{job.job_name}]')
    # do the preliminary check to make sure jobs are not overlapping with multiple servers
    # All the cluster related work goes here
    # -------------------->
    can_i_run_a_batch = do_batch_preliminary_check(job_id=job_id)
    # -------------------->
    logger.info(f'Job [{job.job_name}] can_i_run_a_batch: {can_i_run_a_batch}')
    if can_i_run_a_batch:
        run_batch = list_map_dict.get(job_id)
        job_status, job_content = run_batch()
        status = do_job_update(job_id=job_id, job_status=job_status, job_content=job_content)
        logger.info(f'Job [{job.job_name}] has been updated: {status}')


def batch_job_1():
    logger.info('RUNNING batch_job_1')
    # Testing purpose
    start_time = datetime.now().replace(microsecond=0)
    time.sleep(20)
    end_time = datetime.now().replace(microsecond=0)
    job_content = {
        'success_count': f'{random.randint(10,100)}',
        'failure_count': f'{random.randint(20, 40)}',
        'execution_time': f'{end_time - start_time}'
    }
    return 0, job_content # Returning job as completed


def batch_job_2():
    logger.info('RUNNING batch_job_2')
    # Testing purpose
    start_time = datetime.now().replace(microsecond=0)
    time.sleep(30)
    end_time = datetime.now().replace(microsecond=0)
    job_content = {
        'success_count': f'{random.randint(100, 400)}',
        'failure_count': f'{random.randint(1, 10)}',
        'execution_time': f'{end_time - start_time}'
    }
    return 2, job_content # Returning job as failed


def batch_job_3():
    logger.info('RUNNING batch_job_3')
    # Testing purpose
    start_time = datetime.now().replace(microsecond=0)
    time.sleep(40)
    end_time = datetime.now().replace(microsecond=0)
    job_content = {
        'success_count': f'{random.randint(1000, 5000)}',
        'failure_count': f'{random.randint(100, 120)}',
        'execution_time': f'{end_time - start_time}'
    }
    return 0, job_content # Returning job as completed


# Configure the list of batch jobs
list_map_dict = {
    1: batch_job_1,
    2: batch_job_2,
    3: batch_job_3,
}


def start():
    logger.info('Entering to schedule a batch jobs')
    scheduler = BackgroundScheduler()
    jobs = BatchJob.objects.all()
    # Schedule all the job one by one
    for job in jobs:
        logger.info(f'JOB: [{job.job_id}]=[{job.job_name}] added to scheduler')
        scheduler.add_job(
            func=batch_job_worker,
            trigger=CronTrigger.from_crontab(job.job_cron),
            kwargs={'job_id': job.job_id}
        )

    scheduler.start()
    logger.info(f'Number of jobs added to the schedule: [{len(jobs)}]')
    atexit.register(lambda: scheduler.shutdown(wait=False))
