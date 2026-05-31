from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

def home(request):
    return render(request, 'home.html')

def layanan(request):
    return render(request, 'layanan.html')

def cek_status(request):
    return render(request, 'cek-status.html')

def login_view(request):
    if request.user.is_authenticated:
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
                # Will fail authentication naturally in the next step
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
        # Clean email to serve as username
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
            return redirect('cek_status')
        except Exception as e:
            messages.error(request, 'Terjadi kesalahan sistem saat membuat akun. Silakan coba lagi.')
            
    return render(request, 'register.html')