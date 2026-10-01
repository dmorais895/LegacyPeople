import re
from django import forms
from django.utils.html import strip_tags
from .models import Person

YES_NO_CHOICES = (("yes", "Sim"), ("no", "Não"))

class PersonForm(forms.ModelForm):
    # Explicit choices avoid treating the non-empty string "no" as True.
    has_gc = forms.TypedChoiceField(
        choices=YES_NO_CHOICES, coerce=lambda value: value == "yes",
        empty_value=False, required=False, widget=forms.RadioSelect,
    )
    wants_chat = forms.TypedChoiceField(
        choices=YES_NO_CHOICES, coerce=lambda value: value == "yes",
        empty_value=False, required=False, widget=forms.RadioSelect,
    )
    frequents_legacy = forms.TypedChoiceField(
        choices=YES_NO_CHOICES, coerce=lambda value: value == "yes",
        empty_value=False, required=False, widget=forms.RadioSelect,
    )

    class Meta:
        model = Person
        fields = [
            'name', 'email', 'whatsapp', 'has_gc', 'gc_name',
            'time_lagoinha', 'feeling', 'prayer_request',
            'wants_chat', 'frequents_legacy', 'legacy_reason'
        ]

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        cleaned_name = strip_tags(name).strip()
        if len(cleaned_name) < 2:
            raise forms.ValidationError("Por favor, informe um nome válido.")
        return cleaned_name

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        return strip_tags(email).strip().lower()

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp', '')
        whatsapp = re.sub(r'[\s\-\(\)]', '', whatsapp)
        if not re.match(r'^\+55\d{10,11}$', whatsapp):
            raise forms.ValidationError("Por favor, insira um número válido com o código +55 (Ex: +5511999999999).")
        return whatsapp

    def clean_gc_name(self):
        gc_name = self.cleaned_data.get('gc_name', '')
        if gc_name:
            return strip_tags(gc_name).strip()
        return ''

    def clean_time_lagoinha(self):
        time_lagoinha = self.cleaned_data.get('time_lagoinha', '')
        allowed_options = ['menos_6_meses', '6_meses_1_ano', '1_3_anos', 'mais_3_anos']
        cleaned_val = strip_tags(time_lagoinha).strip()
        if cleaned_val not in allowed_options:
            raise forms.ValidationError("Opção de tempo em Lagoinha inválida.")
        return cleaned_val

    def clean_prayer_request(self):
        prayer_request = self.cleaned_data.get('prayer_request', '')
        if prayer_request:
            cleaned_req = strip_tags(prayer_request).strip()
            if len(cleaned_req) > 2000:
                raise forms.ValidationError("O pedido de oração não pode exceder 2000 caracteres.")
            return cleaned_req
        return ''

    def clean_legacy_reason(self):
        legacy_reason = self.cleaned_data.get('legacy_reason', '')
        if legacy_reason:
            cleaned_reason = strip_tags(legacy_reason).strip()
            if len(cleaned_reason) > 2000:
                raise forms.ValidationError("O texto não pode exceder 2000 caracteres.")
            return cleaned_reason
        return ''

    def clean(self):
        cleaned_data = super().clean()
        has_gc = cleaned_data.get('has_gc')
        frequents_legacy = cleaned_data.get('frequents_legacy')

        if not has_gc:
            cleaned_data['gc_name'] = ''

        if frequents_legacy:
            cleaned_data['legacy_reason'] = ''

        return cleaned_data
