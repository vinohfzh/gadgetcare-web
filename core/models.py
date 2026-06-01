from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('pelanggan', 'Pelanggan'),
        ('teknisi', 'Teknisi'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='pelanggan')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('menunggu', 'Menunggu'),
        ('diagnosa', 'Diagnosa'),
        ('perbaikan', 'Proses Perbaikan'),
        ('selesai', 'Selesai'),
    )
    PRIORITY_CHOICES = (
        ('tinggi', 'Tinggi'),
        ('normal', 'Normal'),
        ('rendah', 'Rendah'),
    )
    
    ticket_number = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=100, default='Pelanggan')
    customer_phone = models.CharField(max_length=20, blank=True, null=True, default='')
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50) # e.g. Laptop, Smartphone, Tablet
    complaint = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='menunggu')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    estimation = models.CharField(max_length=50, default='2 - 3 Hari')
    cost = models.IntegerField(default=0)
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ticket_number} - {self.device_name}"

class ActivityLog(models.Model):
    ICON_CHOICES = (
        ('green', 'Green'),
        ('blue', 'Blue'),
        ('red', 'Red'),
    )
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon_type = models.CharField(max_length=10, choices=ICON_CHOICES, default='blue')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.get_or_create(user=instance)

class SparePart(models.Model):
    CATEGORY_CHOICES = (
        ('layar', 'Layar / LCD'),
        ('baterai', 'Baterai'),
        ('mesin', 'Motherboard / Mesin'),
        ('kamera', 'Kamera'),
        ('konektor', 'Konektor Charger'),
        ('fleksibel', 'Kabel Fleksibel'),
        ('tombol', 'Tombol Fisik'),
        ('aksesoris', 'Aksesoris / Case'),
        ('lainnya', 'Lain-lain'),
    )
    
    DEVICE_CHOICES = (
        ('smartphone', 'Smartphone'),
        ('laptop', 'Laptop'),
        ('tablet', 'Tablet'),
        ('lainnya', 'Lain-lain'),
    )

    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='lainnya')
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES, default='lainnya')
    stock = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=5)
    cost_price = models.IntegerField(default=0)  # Harga Beli (Rp)
    sell_price = models.IntegerField(default=0)  # Harga Jual (Rp)
    location = models.CharField(max_length=50, blank=True, null=True)  # Lokasi Rak/Box
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.min_stock

    @property
    def is_out_of_stock(self):
        return self.stock <= 0

class SparePartUsage(models.Model):
    ACTIVITY_CHOICES = (
        ('tambah', 'Restock / Tambah'),
        ('pakai', 'Digunakan'),
        ('penyesuaian', 'Penyesuaian'),
    )

    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='usages')
    ticket = models.ForeignKey('Ticket', on_delete=models.SET_NULL, null=True, blank=True, related_name='part_usages')
    quantity = models.IntegerField()  # Positif untuk restock, negatif untuk pengurangan/pemakaian
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='penyesuaian')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.spare_part.name} - {self.get_activity_type_display()} ({self.quantity})"

