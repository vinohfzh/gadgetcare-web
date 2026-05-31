import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Ticket, ActivityLog

class Command(BaseCommand):
    help = 'Seeds the database with GadgetCare initial data (users, profiles, tickets, and activity logs)'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        
        # Clear tickets and activity logs
        Ticket.objects.all().delete()
        ActivityLog.objects.all().delete()

        # 1. Create or update users
        self.stdout.write('Creating users and user profiles...')
        
        # Create Technician user: Rasya Mahendra
        tech_user, created = User.objects.get_or_create(
            username='rasya',
            defaults={
                'email': 'rasya@gadgetcare.com',
                'first_name': 'Rasya',
                'last_name': 'Mahendra',
                'is_staff': True
            }
        )
        tech_user.set_password('password123')
        tech_user.save()
        
        # Ensure profile exists and has role 'teknisi'
        tech_profile, _ = UserProfile.objects.get_or_create(user=tech_user)
        tech_profile.role = 'teknisi'
        tech_profile.phone = '081234567890'
        tech_profile.save()

        # Create Pelanggan (Customer) user: Vino Ganteng
        cust_user, created = User.objects.get_or_create(
            username='vino',
            defaults={
                'email': 'vino@gmail.com',
                'first_name': 'Vino',
                'last_name': 'Ganteng',
                'is_staff': False
            }
        )
        cust_user.set_password('password123')
        cust_user.save()
        
        # Ensure profile exists and has role 'pelanggan'
        cust_profile, _ = UserProfile.objects.get_or_create(user=cust_user)
        cust_profile.role = 'pelanggan'
        cust_profile.phone = '089876543210'
        cust_profile.save()

        self.stdout.write(f'Users created: Technician "{tech_user.username}", Customer "{cust_user.username}".')

        # 2. Create Tickets
        self.stdout.write('Creating tickets...')

        tickets_data = [
            # Diagnosa Tickets (Assigned to Rasya)
            {
                'ticket_number': 'tkt-8902',
                'device_name': 'Macbook Pro M1 - Layar Berkedip',
                'device_type': 'Laptop',
                'complaint': 'Layar berkedip secara acak saat tingkat kecerahan di bawah 50%.',
                'status': 'diagnosa',
                'priority': 'tinggi',
                'estimation': '2 - 3 Hari',
                'technician': tech_user
            },
            {
                'ticket_number': 'tkt-8903',
                'device_name': 'iPhone 13 Pro - Ganti LCD',
                'device_type': 'Smartphone',
                'complaint': 'Layar retak akibat terjatuh dan respon sentuhan tidak bekerja di area tengah.',
                'status': 'diagnosa',
                'priority': 'tinggi',
                'estimation': '1 - 2 Hari',
                'technician': tech_user
            },
            # Proses Perbaikan Tickets (Assigned to Rasya)
            {
                'ticket_number': 'tkt-8802',
                'device_name': 'Macbook Pro M1 - Layar Berkedip',
                'device_type': 'Laptop',
                'complaint': 'Layar berkedip secara acak, sedang dilakukan perbaikan pada flex cable / konektor LCD.',
                'status': 'perbaikan',
                'priority': 'normal',
                'estimation': '2 - 3 Hari',
                'technician': tech_user
            },
            # Menunggu Tickets (Unassigned / Claimable)
            {
                'ticket_number': 'tkt-8701',
                'device_name': 'Asus Rog Zephyrus',
                'device_type': 'Laptop',
                'complaint': 'Overheat saat main game berat, kipas/fan berisik dan bergetar kencang.',
                'status': 'menunggu',
                'priority': 'tinggi',
                'estimation': '2 - 3 Hari',
                'technician': None
            },
            {
                'ticket_number': 'tkt-8702',
                'device_name': 'iPad Air 5',
                'device_type': 'Tablet',
                'complaint': 'Baterai sangat boros dan perangkat cepat panas saat digunakan untuk menggambar.',
                'status': 'menunggu',
                'priority': 'normal',
                'estimation': '1 - 2 Hari',
                'technician': None
            },
            {
                'ticket_number': 'tkt-8703',
                'device_name': 'Sony WH-1000XM4',
                'device_type': 'Aksesoris',
                'complaint': 'Active Noise Cancelling mati sebelah kiri dan suara berdengung setelah terkena cipratan air.',
                'status': 'menunggu',
                'priority': 'rendah',
                'estimation': '3 - 4 Hari',
                'technician': None
            },
            {
                'ticket_number': 'tkt-8704',
                'device_name': 'Samsung Galaxy S23 Ultra',
                'device_type': 'Smartphone',
                'complaint': 'Kamera belakang buram/blur dan autofokus tidak berfungsi setelah terjatuh.',
                'status': 'menunggu',
                'priority': 'tinggi',
                'estimation': '1 - 2 Hari',
                'technician': None
            },
            # Selesai Tickets
            {
                'ticket_number': 'tkt-8885',
                'device_name': 'iPad Air 5',
                'device_type': 'Tablet',
                'complaint': 'Ganti baterai karena battery health drop di bawah 70% dan sering mati mendadak.',
                'status': 'selesai',
                'priority': 'normal',
                'estimation': 'Selesai',
                'technician': tech_user
            }
        ]

        for ticket_info in tickets_data:
            Ticket.objects.create(**ticket_info)

        self.stdout.write(f'Created {len(tickets_data)} sample tickets.')

        # 3. Create Activity Logs
        self.stdout.write('Creating activity logs...')

        activities_data = [
            {
                'title': 'Tiket #tkt-8885 Ditutup',
                'description': 'Penggantian baterai iPad Air berhasil diselesaikan.',
                'icon_type': 'green'
            },
            {
                'title': 'Suku Cadang Tiba',
                'description': 'LCD untuk iPhone 13 Pro (Tiket #tkt-8903) telah diterima.',
                'icon_type': 'blue'
            },
            {
                'title': 'Tiket Mendesak Baru',
                'description': 'Layar MacBook Pro M1 berkedip. Masuk ke antrean belum ditugaskan.',
                'icon_type': 'red'
            }
        ]

        for act_info in activities_data:
            ActivityLog.objects.create(**act_info)

        self.stdout.write(f'Created {len(activities_data)} activity logs.')
        self.stdout.write(self.style.SUCCESS('Successfully seeded GadgetCare database!'))
