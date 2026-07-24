from django.core.management.base import BaseCommand
from dosen.models import Dosen


class Command(BaseCommand):
    help = "Hitung ulang dan simpan TMT Pensiun untuk semua dosen"

    def handle(self, *args, **options):
        total = 0
        for dosen in Dosen.objects.all():
            tmt_baru = dosen.hitung_tmt_pensiun()
            if tmt_baru != dosen.tmt_pensiun:
                Dosen.objects.filter(pk=dosen.pk).update(tmt_pensiun=tmt_baru)
                total += 1
        self.stdout.write(self.style.SUCCESS(f"{total} data dosen diperbarui."))