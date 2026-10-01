from django.db import models
from django.core.validators import RegexValidator

TIME_LAGOINHA_CHOICES = [
    ('menos_6_meses', 'Menos de 6 meses'),
    ('6_meses_1_ano', 'Entre 6 meses e 1 ano'),
    ('1_3_anos', 'Entre 1 e 3 anos'),
    ('mais_3_anos', 'Mais de 3 anos'),
]

class RateLimit(models.Model):
    """Shared fixed-window counters, updated atomically by all application workers."""

    key = models.CharField(max_length=100, primary_key=True)
    attempts = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)

    def __str__(self):
        return self.key

class Person(models.Model):
    FEELING_CHOICES = [
        (1, 'Ótimo'),
        (2, 'Bem'),
        (3, 'Neutro'),
        (4, 'Não muito bem'),
        (5, 'Mal'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nome Completo")
    email = models.EmailField(verbose_name="Endereço de E-mail")

    whatsapp_regex = RegexValidator(
        regex=r'^\+55\d{10,11}$',
        message="O número deve estar no formato: +5511999999999 (apenas números)"
    )
    whatsapp = models.CharField(validators=[whatsapp_regex], max_length=20, verbose_name="Número de WhatsApp")

    has_gc = models.BooleanField(default=False, verbose_name="Faz parte de um GC?")
    # Max length guards against excessively large payloads stored in the database
    gc_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Qual Grupo de Crescimento?")

    # choices enforced at the ORM layer for defence-in-depth beyond form validation
    time_lagoinha = models.CharField(
        max_length=50,
        choices=TIME_LAGOINHA_CHOICES,
        verbose_name="Tempo em Lagoinha"
    )

    feeling = models.IntegerField(choices=FEELING_CHOICES, verbose_name="Como você está se sentindo?")

    # Explicit max_length on TextFields prevents unbounded storage DoS
    prayer_request = models.TextField(blank=True, max_length=2000, verbose_name="Pedido de oração")

    wants_chat = models.BooleanField(default=False, verbose_name="Gostaria de conversar?")

    frequents_legacy = models.BooleanField(default=True, verbose_name="Frequenta o culto Legacy/programações?")
    legacy_reason = models.TextField(blank=True, max_length=2000, verbose_name="O que te faria se interessar mais?")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"

    @property
    def whatsapp_clean(self):
        """Returns digits-only whatsapp number for wa.me API link."""
        return ''.join(filter(str.isdigit, self.whatsapp))
