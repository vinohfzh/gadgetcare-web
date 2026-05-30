from django.urls import path
from .views import home, layanan

urlpatterns = [
    path('', home, name='home'),
    path('layanan/', layanan, name='layanan'),
]