from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Ticket, ActivityLog, SparePart, SparePartUsage

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

@login_required
def daftar_perbaikan(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses untuk halaman ini.')
        return redirect('cek_status')
        
    from django.db.models import Q
    from django.core.paginator import Paginator
    from django.utils import timezone
    
    tickets_list = Ticket.objects.filter(technician=request.user).order_by('-updated_at')
    
    q = request.GET.get('q', '').strip()
    if q:
        tickets_list = tickets_list.filter(
            Q(ticket_number__icontains=q) |
            Q(device_name__icontains=q) |
            Q(customer_name__icontains=q) |
            Q(complaint__icontains=q)
        )
        
    total_antrian = Ticket.objects.filter(technician=request.user).exclude(status='selesai').count()
    sedang_diproses = Ticket.objects.filter(technician=request.user, status='perbaikan').count()
    
    today = timezone.localdate()
    selesai_hari_ini = Ticket.objects.filter(
        technician=request.user,
        status='selesai',
        updated_at__date=today
    ).count()
    
    paginator = Paginator(tickets_list, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    available_tickets = Ticket.objects.filter(status='menunggu', technician__isnull=True)
    
    context = {
        'tickets': page_obj,
        'q': q,
        'total_antrian': total_antrian,
        'sedang_diproses': sedang_diproses,
        'selesai_hari_ini': selesai_hari_ini,
        'available_tickets': available_tickets,
    }
    
    return render(request, 'dashboard-teknisi-perbaikan.html', context)


# ==========================================
# INVENTORY / SPARE PARTS VIEWS
# ==========================================

@login_required
def dashboard_inventoris(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses untuk halaman ini.')
        return redirect('cek_status')
        
    from django.db.models import Q, Sum
    from django.core.paginator import Paginator
    
    # Base Queryset
    parts_list = SparePart.objects.all().order_by('name')
    
    # 1. Search Query
    q = request.GET.get('q', '').strip()
    if q:
        parts_list = parts_list.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(location__icontains=q)
        )
        
    # 2. Category Filter
    category = request.GET.get('category', '').strip()
    if category:
        parts_list = parts_list.filter(category=category)
        
    # 3. Device Type Filter
    device_type = request.GET.get('device_type', '').strip()
    if device_type:
        parts_list = parts_list.filter(device_type=device_type)
        
    # 4. Stock Status Filter
    stock_status = request.GET.get('stock_status', '').strip()
    if stock_status == 'low':
        parts_list = [p for p in parts_list if p.is_low_stock]
    elif stock_status == 'out':
        parts_list = [p for p in parts_list if p.is_out_of_stock]
    
    # Calculated Statistics
    all_parts = SparePart.objects.all()
    total_items = all_parts.count()
    
    # Sum of stock
    total_stock = all_parts.aggregate(total=Sum('stock'))['total'] or 0
    
    # Low stock & Out of stock counts
    low_stock_count = 0
    out_of_stock_count = 0
    inventory_value = 0
    
    for p in all_parts:
        if p.is_out_of_stock:
            out_of_stock_count += 1
        elif p.is_low_stock:
            low_stock_count += 1
        inventory_value += (p.stock * p.cost_price)
        
    # Available tickets for Sidebar badge count
    available_tickets = Ticket.objects.filter(status='menunggu', technician__isnull=True)
    
    # Pagination
    paginator = Paginator(parts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'parts': page_obj,
        'q': q,
        'selected_category': category,
        'selected_device': device_type,
        'selected_stock_status': stock_status,
        
        # Choice tuples for forms/filters
        'category_choices': SparePart.CATEGORY_CHOICES,
        'device_choices': SparePart.DEVICE_CHOICES,
        
        # Stats
        'total_items': total_items,
        'total_stock': total_stock,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'inventory_value': inventory_value,
        
        'available_tickets': available_tickets,
    }
    
    return render(request, 'dashboard-inventoris.html', context)


@login_required
def tambah_sparepart(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses.')
        return redirect('cek_status')
        
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        sku = request.POST.get('sku', '').strip().upper()
        category = request.POST.get('category', '').strip()
        device_type = request.POST.get('device_type', '').strip()
        stock = int(request.POST.get('stock', 0) or 0)
        min_stock = int(request.POST.get('min_stock', 5) or 5)
        cost_price = int(request.POST.get('cost_price', 0) or 0)
        sell_price = int(request.POST.get('sell_price', 0) or 0)
        location = request.POST.get('location', '').strip()
        
        if not name or not sku:
            messages.error(request, 'Nama dan SKU wajib diisi.')
            return redirect('dashboard_inventoris')
            
        if SparePart.objects.filter(sku=sku).exists():
            messages.error(request, f'Sukucadang dengan SKU {sku} sudah terdaftar.')
            return redirect('dashboard_inventoris')
            
        try:
            part = SparePart.objects.create(
                name=name, sku=sku, category=category, device_type=device_type,
                stock=stock, min_stock=min_stock, cost_price=cost_price,
                sell_price=sell_price, location=location
            )
            
            # Create Stock Movement if initial stock is > 0
            if stock > 0:
                SparePartUsage.objects.create(
                    spare_part=part,
                    quantity=stock,
                    activity_type='tambah',
                    notes='Stok awal pendaftaran barang baru.'
                )
                
            # Log Activity
            tech_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            ActivityLog.objects.create(
                title=f"Sukucadang {sku} Didaftarkan",
                description=f"{tech_name} mendaftarkan sukucadang baru: {name} dengan stok {stock}.",
                icon_type='green'
            )
            
            messages.success(request, f'Sukucadang {name} ({sku}) berhasil ditambahkan.')
        except Exception as e:
            messages.error(request, f'Gagal menambahkan sukucadang: {str(e)}')
            
    return redirect('dashboard_inventoris')


@login_required
def edit_sparepart(request, part_id):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses.')
        return redirect('cek_status')
        
    part = get_object_or_404(SparePart, id=part_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        sku = request.POST.get('sku', '').strip().upper()
        category = request.POST.get('category', '').strip()
        device_type = request.POST.get('device_type', '').strip()
        min_stock = int(request.POST.get('min_stock', 5) or 5)
        cost_price = int(request.POST.get('cost_price', 0) or 0)
        sell_price = int(request.POST.get('sell_price', 0) or 0)
        location = request.POST.get('location', '').strip()
        new_stock = int(request.POST.get('stock', part.stock) or part.stock)
        
        if not name or not sku:
            messages.error(request, 'Nama dan SKU wajib diisi.')
            return redirect('dashboard_inventoris')
            
        # Check SKU uniqueness if changed
        if sku != part.sku and SparePart.objects.filter(sku=sku).exists():
            messages.error(request, f'SKU {sku} sudah digunakan barang lain.')
            return redirect('dashboard_inventoris')
            
        try:
            # Check if stock changed to create usage record
            stock_diff = new_stock - part.stock
            
            part.name = name
            part.sku = sku
            part.category = category
            part.device_type = device_type
            part.min_stock = min_stock
            part.cost_price = cost_price
            part.sell_price = sell_price
            part.location = location
            part.stock = new_stock
            part.save()
            
            if stock_diff != 0:
                act_type = 'tambah' if stock_diff > 0 else 'pakai'
                SparePartUsage.objects.create(
                    spare_part=part,
                    quantity=stock_diff,
                    activity_type=act_type,
                    notes='Penyesuaian stok manual dari menu edit.'
                )
                
            messages.success(request, f'Data sukucadang {name} berhasil diperbarui.')
        except Exception as e:
            messages.error(request, f'Gagal memperbarui sukucadang: {str(e)}')
            
    return redirect('dashboard_inventoris')


@login_required
def hapus_sparepart(request, part_id):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses.')
        return redirect('cek_status')
        
    part = get_object_or_404(SparePart, id=part_id)
    
    try:
        name = part.name
        sku = part.sku
        part.delete()
        
        # Log Activity
        tech_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        ActivityLog.objects.create(
            title=f"Sukucadang {sku} Dihapus",
            description=f"{tech_name} menghapus sukucadang: {name} ({sku}) dari sistem.",
            icon_type='red'
        )
        
        messages.success(request, f'Sukucadang {name} ({sku}) berhasil dihapus.')
    except Exception as e:
        messages.error(request, f'Gagal menghapus sukucadang: {str(e)}')
        
    return redirect('dashboard_inventoris')


@login_required
def adjust_stock(request, part_id, direction):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses.')
        return redirect('cek_status')
        
    part = get_object_or_404(SparePart, id=part_id)
    
    try:
        qty = 0
        if direction == 'up':
            qty = 1
            part.stock += 1
            act_type = 'tambah'
            notes = 'Penyesuaian instan: Stok ditambah 1 unit.'
        elif direction == 'down':
            if part.stock <= 0:
                messages.error(request, f'Stok {part.name} sudah kosong, tidak bisa dikurangi.')
                return redirect('dashboard_inventoris')
            qty = -1
            part.stock -= 1
            act_type = 'pakai'
            notes = 'Penyesuaian instan: Stok dikurangi 1 unit.'
        else:
            messages.error(request, 'Penyesuaian tidak valid.')
            return redirect('dashboard_inventoris')
            
        part.save()
        
        # Log stock movement
        SparePartUsage.objects.create(
            spare_part=part,
            quantity=qty,
            activity_type=act_type,
            notes=notes
        )
        
        messages.success(request, f'Stok {part.name} berhasil diperbarui ({part.stock} unit).')
    except Exception as e:
        messages.error(request, f'Gagal menyesuaikan stok: {str(e)}')
        
    return redirect('dashboard_inventoris')


@login_required
def riwayat_inventoris(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses untuk halaman ini.')
        return redirect('cek_status')
        
    from django.core.paginator import Paginator
    
    # Get all usages / movements
    usages_list = SparePartUsage.objects.all().order_by('-created_at')
    
    # Filter by search
    q = request.GET.get('q', '').strip()
    if q:
        from django.db.models import Q
        usages_list = usages_list.filter(
            Q(spare_part__name__icontains=q) |
            Q(spare_part__sku__icontains=q) |
            Q(notes__icontains=q)
        )
        
    # Filter by activity type
    activity_type = request.GET.get('activity_type', '').strip()
    if activity_type:
        usages_list = usages_list.filter(activity_type=activity_type)
        
    # Paginator
    paginator = Paginator(usages_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    available_tickets = Ticket.objects.filter(status='menunggu', technician__isnull=True)
    
    context = {
        'usages': page_obj,
        'q': q,
        'selected_activity': activity_type,
        'activity_choices': SparePartUsage.ACTIVITY_CHOICES,
        'available_tickets': available_tickets,
    }
    
    return render(request, 'dashboard-inventoris-riwayat.html', context)


@login_required
def dashboard_pengaturan(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses untuk halaman ini.')
        return redirect('cek_status')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            if not full_name or not email:
                messages.error(request, 'Nama Lengkap dan Email wajib diisi.')
                return redirect('dashboard_pengaturan')
                
            # Split full name
            names = full_name.split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''
            
            # Check email uniqueness
            if User.objects.filter(email__iexact=email).exclude(id=request.user.id).exists():
                messages.error(request, 'Alamat email ini sudah digunakan oleh akun lain.')
                return redirect('dashboard_pengaturan')
                
            try:
                # Save User details
                user = request.user
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save()
                
                # Save Profile details
                profile = request.user.profile
                profile.phone = phone
                profile.save()
                
                # Create Activity Log
                tech_name = f"{user.first_name} {user.last_name}".strip() or user.username
                ActivityLog.objects.create(
                    title="Profil Diperbarui",
                    description=f"Teknisi {tech_name} memperbarui informasi profil pribadinya.",
                    icon_type='blue'
                )
                
                messages.success(request, 'Profil pribadi Anda berhasil diperbarui.')
            except Exception as e:
                messages.error(request, f'Gagal memperbarui profil: {str(e)}')
                
        elif action == 'update_password':
            from django.contrib.auth import update_session_auth_hash
            
            old_password = request.POST.get('old_password', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            
            if not old_password or not new_password or not confirm_password:
                messages.error(request, 'Semua kolom kata sandi wajib diisi.')
                return redirect('dashboard_pengaturan')
                
            if not request.user.check_password(old_password):
                messages.error(request, 'Kata sandi saat ini salah.')
                return redirect('dashboard_pengaturan')
                
            if len(new_password) < 6:
                messages.error(request, 'Kata sandi baru minimal harus terdiri dari 6 karakter.')
                return redirect('dashboard_pengaturan')
                
            if new_password != confirm_password:
                messages.error(request, 'Konfirmasi kata sandi baru tidak cocok.')
                return redirect('dashboard_pengaturan')
                
            try:
                user = request.user
                user.set_password(new_password)
                user.save()
                
                # Update session to prevent logout
                update_session_auth_hash(request, user)
                
                # Create Activity Log
                tech_name = f"{user.first_name} {user.last_name}".strip() or user.username
                ActivityLog.objects.create(
                    title="Kata Sandi Diubah",
                    description=f"Teknisi {tech_name} berhasil mengubah kata sandinya.",
                    icon_type='red'
                )
                
                messages.success(request, 'Kata sandi Anda berhasil diperbarui.')
            except Exception as e:
                messages.error(request, f'Gagal memperbarui kata sandi: {str(e)}')
                
        return redirect('dashboard_pengaturan')
        
    # GET request
    available_tickets = Ticket.objects.filter(status='menunggu', technician__isnull=True)
    full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    
    context = {
        'full_name': full_name,
        'available_tickets': available_tickets,
    }
    
    return render(request, 'dashboard-teknisi-pengaturan.html', context)


@login_required
def dashboard_laporan(request):
    # Authorization check
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teknisi':
        messages.error(request, 'Anda tidak memiliki hak akses untuk halaman ini.')
        return redirect('cek_status')
    
    from django.utils import timezone
    from django.db.models import Sum, Q, Avg
    from django.core.paginator import Paginator
    import csv
    from django.http import HttpResponse
    
    # 1. Base Query - Completed repairs for this technician
    completed_tickets = Ticket.objects.filter(status='selesai', technician=request.user).order_by('-updated_at')
    
    # 2. Date Filtering
    date_filter = request.GET.get('date_filter', 'all').strip()
    now = timezone.now()
    
    if date_filter == '7_days':
        start_date = now - timezone.timedelta(days=7)
        completed_tickets = completed_tickets.filter(updated_at__gte=start_date)
    elif date_filter == '30_days':
        start_date = now - timezone.timedelta(days=30)
        completed_tickets = completed_tickets.filter(updated_at__gte=start_date)
    elif date_filter == 'this_month':
        completed_tickets = completed_tickets.filter(updated_at__year=now.year, updated_at__month=now.month)
    
    # 3. Search Query Filtering
    q = request.GET.get('q', '').strip()
    if q:
        completed_tickets = completed_tickets.filter(
            Q(ticket_number__icontains=q) |
            Q(customer_name__icontains=q) |
            Q(device_name__icontains=q)
        )
        
    # 4. Device Type Filtering
    selected_device_type = request.GET.get('device_type', '').strip()
    if selected_device_type:
        completed_tickets = completed_tickets.filter(device_type=selected_device_type)
        
    # 5. CSV Export Action
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="Laporan_Servis_GC_{timezone.localdate()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID Tiket', 'Pelanggan', 'No. Telepon', 'Perangkat', 'Tipe Perangkat', 'Keluhan', 'Tanggal Selesai', 'Biaya (Rp)'])
        
        for t in completed_tickets:
            date_str = timezone.localtime(t.updated_at).strftime('%Y-%m-%d %H:%M')
            writer.writerow([
                t.ticket_number,
                t.customer_name,
                t.customer_phone or '',
                t.device_name,
                t.device_type,
                t.complaint,
                date_str,
                t.cost
            ])
        return response
        
    # 6. Calculate Metrics (month-to-date and all-time stats)
    tech_all_completed = Ticket.objects.filter(status='selesai', technician=request.user)
    
    # Bulan ini (Total selesai)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    selesai_bulan_ini = tech_all_completed.filter(updated_at__gte=month_start).count()
    
    # Total pendapatan (bulan ini vs total)
    pendapatan_bulan_ini = tech_all_completed.filter(updated_at__gte=month_start).aggregate(total=Sum('cost'))['total'] or 0
    total_pendapatan = tech_all_completed.aggregate(total=Sum('cost'))['total'] or 0
    
    # Rata-rata biaya servis
    avg_cost = tech_all_completed.aggregate(avg=Avg('cost'))['avg'] or 0
    
    # Perbaikan aktif (sedang dalam perbaikan atau diagnosa)
    perbaikan_aktif_count = Ticket.objects.filter(
        technician=request.user,
        status__in=['diagnosa', 'perbaikan']
    ).count()
    
    # 7. Device type choices for filter dropdown
    device_types = Ticket.objects.filter(technician=request.user).values_list('device_type', flat=True).distinct()
    device_types = [dt for dt in device_types if dt]
    
    # 8. Charts Data Calculation
    # Chart 1: Completed repairs trend (last 7 days)
    days_labels = []
    days_counts = []
    for i in range(6, -1, -1):
        target_day = timezone.localdate() - timezone.timedelta(days=i)
        day_count = tech_all_completed.filter(updated_at__date=target_day).count()
        days_labels.append(target_day.strftime('%d %b'))
        days_counts.append(day_count)
        
    # Chart 2: Device distribution percentages (Top 3 + Others)
    device_counts = {}
    total_devices = tech_all_completed.count()
    if total_devices > 0:
        for dt in tech_all_completed.values_list('device_type', flat=True):
            if dt:
                device_counts[dt] = device_counts.get(dt, 0) + 1
        
        # Sort and take top 3
        sorted_devices = sorted(device_counts.items(), key=lambda x: x[1], reverse=True)
        top_devices = sorted_devices[:3]
        others_count = sum(x[1] for x in sorted_devices[3:])
        
        chart_device_data = []
        for name, count in top_devices:
            pct = round((count / total_devices) * 100)
            chart_device_data.append({'name': name, 'count': count, 'pct': pct})
        if others_count > 0:
            pct = round((others_count / total_devices) * 100)
            chart_device_data.append({'name': 'Lain-lain', 'count': others_count, 'pct': pct})
    else:
        chart_device_data = []
        
    # 9. Pagination
    paginator = Paginator(completed_tickets, 10)  # Show 10 completed repairs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    available_tickets = Ticket.objects.filter(status='menunggu', technician__isnull=True)
    
    context = {
        'tickets': page_obj,
        'q': q,
        'date_filter': date_filter,
        'selected_device_type': selected_device_type,
        'device_types': device_types,
        
        # Metrics
        'selesai_bulan_ini': selesai_bulan_ini,
        'pendapatan_bulan_ini': pendapatan_bulan_ini,
        'total_pendapatan': total_pendapatan,
        'avg_cost': avg_cost,
        'perbaikan_aktif_count': perbaikan_aktif_count,
        
        # Chart Data
        'chart_days_labels': days_labels,
        'chart_days_counts': days_counts,
        'chart_device_data': chart_device_data,
        
        'available_tickets': available_tickets,
    }
    
    return render(request, 'dashboard-teknisi-laporan.html', context)