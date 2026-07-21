import re

from django import forms
from .models import Person

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            'name', 'email', 'whatsapp', 'has_gc', 'gc_name',
            'time_lagoinha', 'feeling', 'prayer_request',
            'wants_chat', 'frequents_legacy', 'legacy_reason'
        ]

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp', '')
        # Remove any spaces, dashes, or parentheses
        whatsapp = re.sub(r'[\s\-\(\)]', '', whatsapp)

        # Verify the format starts with +55 and has 10 or 11 digits
        if not re.match(r'^\+55\d{10,11}$', whatsapp):
            raise forms.ValidationError("Por favor, insira um número válido com o código +55 (Ex: +5511999999999).")
        return whatsapp
