from django.urls import path
from .views import OcrTextExtractView

urlpatterns = [
    path('decode/', OcrTextExtractView.as_view()),
]