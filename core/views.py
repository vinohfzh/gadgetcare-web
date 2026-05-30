from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def layanan(request):
    return render(request, 'layanan.html')