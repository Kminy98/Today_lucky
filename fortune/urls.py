from django.urls import path
from .views import fortune_api

urlpatterns = [
    path("api/fortune", fortune_api),
]
