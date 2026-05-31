from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Ticket, ActivityLog

def home(request):
    return render(request, 'home.html')

def layanan(request):
    return render(request, 'layanan.html')

def cek_status(request):
    return render(request, 'cek-status.html')

def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'teknisi':
            return redirect('dashboard_teknisi')
        return redirect('cek_status')
    
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()  # email or username
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me') == 'on'
        
        if not identifier or not password:
            messages.error(request, 'Silakan masukkan email/username dan password.')
            return render(request, 'login.html')
        
        username = identifier
        # If user entered an email, find their actual username in the database
        if '@' in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                username = user_obj.username
            except User.DoesNotExist:
                pass
                
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Handle "Remember me" session longevity
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks in seconds
            else:
                request.session.set_expiry(0)  # browser session close
                
            messages.success(request, f'Selamat datang kembali, {user.first_name or user.username}!')
            
            if hasattr(user, 'profile') and user.profile.role == 'teknisi':
                return redirect('dashboard_teknisi')
            return redirect('cek_status')
        else:
            messages.error(request, 'Email/Username atau password salah. Silakan coba lagi.')
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Anda telah berhasil keluar.')
    return redirect('home')

def register_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'teknisi':
            return redirect('dashboard_teknisi')
        return redirect('cek_status')
        
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not full_name or not email or not password or not confirm_password:
            messages.error(request, 'Semua kolom pendaftaran wajib diisi.')
            return render(request, 'register.html')
            
        if len(password) < 6:
            messages.error(request, 'Password minimal harus terdiri dari 6 karakter.')
            return render(request, 'register.html')
            
        if password != confirm_password:
            messages.error(request, 'Konfirmasi password tidak cocok.')
            return render(request, 'register.html')
            
        # Check if email is already in use
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Alamat email ini sudah terdaftar. Silakan login.')
            return render(request, 'register.html')
            
        # Create user
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        # Split full name into first and last name
        names = full_name.split(' ', 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ''
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            # Log the user in immediately
            login(request, user)
            messages.success(request, f'Pendaftaran berhasil! Selamat datang, {first_name}!')
            
            if hasattr(user, 'profile') and user.profile.role == 'teknisi':
                return redirect('dashboard_teknisi')
            return redirect('cek_status')
        except Exception as e:
            messages.error(request, 'Terjadi kesalahan sistem saat membuat akun. Silakan coba lagi.')
            
    return render(request, 'register.html')


# Technician Dashboard views
@login_required
def dashboard_teknisi(request):
    # Authorization check
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses untuk halaman ini.')
        return redirect('cek_status')
    
    # Calculate counters
    menunggu_count = Ticket.objects.filter(status='menunggu').count()
    diagnosa_count = Ticket.objects.filter(status='diagnosa', technician=request.user).count()
    perbaikan_count = Ticket.objects.filter(status='perbaikan', technician=request.user).count()
    selesai_hari_ini_count = Ticket.objects.filter(status='selesai', technician=request.user).count()
    
    # Active workflow lists
    diagnosa_tickets = Ticket.objects.filter(status='diagnosa', technician=request.user).order_by('-updated_at')
    perbaikan_tickets = Ticket.objects.filter(status='perbaikan', technician=request.user).order_by('-updated_at')
    
    # Claimable tickets (unassigned)
    available_tickets = Ticket.objects.filter(status='menunggu', technician__isnull=True).order_by('created_at')
    
    # Recent Activities
    activities = ActivityLog.objects.all().order_by('-created_at')[:10]
    
    context = {
        'menunggu_count': menunggu_count,
        'diagnosa_count': diagnosa_count,
        'perbaikan_count': perbaikan_count,
        'selesai_hari_ini_count': selesai_hari_ini_count,
        'diagnosa_tickets': diagnosa_tickets,
        'perbaikan_tickets': perbaikan_tickets,
        'available_tickets': available_tickets,
        'activities': activities,
    }
    
    return render(request, 'dashboard-teknisi.html', context)

@login_required
def claim_ticket(request, ticket_id):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses untuk aksi ini.')
        return redirect('cek_status')
        
    ticket = get_object_or_404(Ticket, id=ticket_id, status='menunggu', technician__isnull=True)
    ticket.technician = request.user
    ticket.status = 'diagnosa'
    ticket.save()
    
    # Create Activity Log
    tech_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    ActivityLog.objects.create(
        title=f"Tiket #{ticket.ticket_number} Diklaim",
        description=f"Teknisi {tech_name} mengambil tanggung jawab perbaikan {ticket.device_name}.",
        icon_type='blue'
    )
    
    messages.success(request, f'Tiket {ticket.ticket_number} ({ticket.device_name}) berhasil Anda ambil untuk didiagnosa!')
    return redirect('dashboard_teknisi')

@login_required
def update_ticket_status(request, ticket_id, new_status):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses untuk aksi ini.')
        return redirect('cek_status')
        
    ticket = get_object_or_404(Ticket, id=ticket_id, technician=request.user)
    
    valid_statuses = dict(Ticket.STATUS_CHOICES)
    if new_status in valid_statuses:
        old_status = ticket.status
        ticket.status = new_status
        ticket.save()
        
        # Log active changes
        tech_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        
        if new_status == 'perbaikan':
            ActivityLog.objects.create(
                title=f"Tiket #{ticket.ticket_number} Diperbaiki",
                description=f"Teknisi {tech_name} mulai melakukan proses perbaikan pada {ticket.device_name}.",
                icon_type='blue'
            )
            messages.success(request, f'Status tiket {ticket.ticket_number} berhasil diubah ke perbaikan.')
        elif new_status == 'selesai':
            ActivityLog.objects.create(
                title=f"Tiket #{ticket.ticket_number} Ditutup",
                description=f"Perbaikan {ticket.device_name} berhasil diselesaikan oleh teknisi {tech_name}.",
                icon_type='green'
            )
            messages.success(request, f'Status tiket {ticket.ticket_number} berhasil diselesaikan!')
        else:
            messages.success(request, f'Status tiket {ticket.ticket_number} diperbarui.')
    else:
        messages.error(request, 'Status perbaikan tidak valid.')
        
    return redirect('dashboard_teknisi')