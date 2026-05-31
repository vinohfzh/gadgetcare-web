from django.urls import path
from .views import home, layanan, cek_status, login_view, logout_view, register_view

urlpatterns = [
    path('', home, name='home'),
    path('layanan/', layanan, name='layanan'),
    path('cek-status/', cek_status, name='cek_status'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
]