from django.urls import path
from schedulerapp import views

urlpatterns = [
    path('', views.view_jobs, name='view_jobs')
]