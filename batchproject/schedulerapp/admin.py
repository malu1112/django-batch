from django.contrib import admin
from schedulerapp.models import BatchJob


class BatchJobAdmin(admin.ModelAdmin):
    list_display = [
        'job_id',
        'job_name',
        'job_enabled',
        'job_cron',
        'job_run_lag_check',
        'job_status',
        'last_updated_ts',
        'job_content'
    ]


admin.site.register(BatchJob, BatchJobAdmin)