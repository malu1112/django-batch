from django.db import models
from django.utils import timezone

STATUS_CHOICES = [
    (0, 'COMPLETED'),
    (1, 'RUNNING'),
    (2, 'FAILED')
]


class BatchJob(models.Model):
    job_id = models.IntegerField(primary_key=True, help_text="Unique Job Id")
    job_name = models.CharField(max_length=150, help_text="Batch job name")
    job_enabled = models.BooleanField(default=True, help_text="Is the job enabled or disabled?")
    job_cron = models.CharField(max_length=250, help_text="Cron Express for a job")
    job_run_lag_check = models.IntegerField(help_text='Running lag check in seconds')
    job_status = models.IntegerField(choices=STATUS_CHOICES)
    job_content = models.TextField(max_length=1200, blank=True, null=True, help_text="Job Completion content")
    last_updated_ts = models.DateTimeField(default=timezone.now, help_text="Job last executed timestamp")

    def __str__(self):
        return f'{self.job_id} {self.job_name} {self.job_status} {self.last_updated_ts}'

    class Meta:
        db_table = "batch_jobs"

