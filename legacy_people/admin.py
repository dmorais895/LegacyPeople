from django.contrib import admin
from .models import Person

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'whatsapp', 'has_gc', 'created_at')
    search_fields = ('name', 'email', 'whatsapp')
    list_filter = ('has_gc', 'feeling', 'wants_chat')
