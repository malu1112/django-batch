from django.shortcuts import render

from schedulerapp.models import BatchJob


def view_jobs(request):
    status = {
        0: 'COMPLETED',
        1: 'RUNNING',
        2: 'FAILED'
    }
    jobs = BatchJob.objects.all()
    for i in jobs:
        i.job_status = status.get(i.job_status)
    return render(request, 'joblist.html', {'jobs': jobs})
