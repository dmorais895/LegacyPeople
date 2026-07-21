from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from legacy_people.models import Person

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with 20 diverse Person records and creates an admin user'

    def handle(self, *args, **options):
        Person.objects.all().delete()

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Admin user created (admin / admin123).'))

        times = ['menos_6_meses', '6_meses_1_ano', '1_3_anos', 'mais_3_anos']
        reasons = ['x', 'y', 'z', 'a', 'b']
        people_data = []

        for i in range(1, 21):
            has_gc = i % 2 == 1
            frequents = i % 2 == 0

            people_data.append(Person(
                name=f"Pessoa Teste {i}",
                email=f"pessoa{i}@example.com",
                whatsapp=f"+551199999{i:04d}",
                has_gc=has_gc,
                gc_name=f"GC {i}" if has_gc else "",
                time_lagoinha=times[(i - 1) % len(times)],
                feeling=((i - 1) % 5) + 1,
                prayer_request="P",
                wants_chat=i % 3 == 0,
                frequents_legacy=frequents,
                legacy_reason="" if frequents else reasons[(i - 1) % len(reasons)]
            ))

        Person.objects.bulk_create(people_data)
        msg = f'Successfully created {len(people_data)} Person records.'
        self.stdout.write(self.style.SUCCESS(msg))
