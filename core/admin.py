from django.contrib import admin
from .models import UserProfile, Ticket, ActivityLog, SparePart, SparePartUsage

admin.site.register(UserProfile)
admin.site.register(Ticket)
admin.site.register(ActivityLog)
admin.site.register(SparePart)
admin.site.register(SparePartUsage)

