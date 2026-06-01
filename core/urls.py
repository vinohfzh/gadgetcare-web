from django.urls import path
from .views import (
    home,
    layanan,
    cek_status,
    login_view,
    logout_view,
    register_view,
    dashboard_teknisi,
    daftar_perbaikan,
    claim_ticket,
    update_ticket_status,
    dashboard_inventoris,
    tambah_sparepart,
    edit_sparepart,
    hapus_sparepart,
    adjust_stock,
    riwayat_inventoris,
    dashboard_pengaturan,
    dashboard_laporan,
)

urlpatterns = [
    path('', home, name='home'),
    path('layanan/', layanan, name='layanan'),
    path('cek-status/', cek_status, name='cek_status'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('dashboard-teknisi/', dashboard_teknisi, name='dashboard_teknisi'),
    path('dashboard-teknisi/perbaikan/', daftar_perbaikan, name='daftar_perbaikan'),
    path('claim-ticket/<int:ticket_id>/', claim_ticket, name='claim_ticket'),
    path('update-ticket-status/<int:ticket_id>/<str:new_status>/', update_ticket_status, name='update_ticket_status'),
    
    # Inventory routes
    path('dashboard-teknisi/inventoris/', dashboard_inventoris, name='dashboard_inventoris'),
    path('dashboard-teknisi/inventoris/tambah/', tambah_sparepart, name='tambah_sparepart'),
    path('dashboard-teknisi/inventoris/edit/<int:part_id>/', edit_sparepart, name='edit_sparepart'),
    path('dashboard-teknisi/inventoris/hapus/<int:part_id>/', hapus_sparepart, name='hapus_sparepart'),
    path('dashboard-teknisi/inventoris/adjust/<int:part_id>/<str:direction>/', adjust_stock, name='adjust_stock'),
    path('dashboard-teknisi/inventoris/riwayat/', riwayat_inventoris, name='riwayat_inventoris'),
    
    # Settings route
    path('dashboard-teknisi/pengaturan/', dashboard_pengaturan, name='dashboard_pengaturan'),
    path('dashboard-teknisi/laporan/', dashboard_laporan, name='dashboard_laporan'),
]