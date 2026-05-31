from django.urls import path
from .views import home, layanan, cek_status, login_view, logout_view, register_view, dashboard_teknisi, claim_ticket, update_ticket_status

urlpatterns = [
    path('', home, name='home'),
    path('layanan/', layanan, name='layanan'),
    path('cek-status/', cek_status, name='cek_status'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('dashboard-teknisi/', dashboard_teknisi, name='dashboard_teknisi'),
    path('claim-ticket/<int:ticket_id>/', claim_ticket, name='claim_ticket'),
    path('update-ticket-status/<int:ticket_id>/<str:new_status>/', update_ticket_status, name='update_ticket_status'),
]