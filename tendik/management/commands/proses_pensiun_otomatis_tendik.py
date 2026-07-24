from django.core.management.base import BaseCommand
from django.utils import timezone
from tendik.models import Tendik, RiwayatBerhentiTendik


class Command(BaseCommand):
    help = "Proses otomatis tendik yang mencapai TMT Pensiun — buat Riwayat Berhenti otomatis"

    def handle(self, *args, **options):
        today = timezone.localdate()

        qs = Tendik.objects.filter(
            tmt_pensiun__isnull=False,
            tmt_pensiun__lte=today,
        ).select_related('riwayat_berhenti')

        total_diproses = 0
        total_dilewati = 0

        for t in qs:
            # RiwayatBerhentiTendik = OneToOneField -> cukup 1 record per tendik
            if hasattr(t, 'riwayat_berhenti'):
                total_dilewati += 1
                continue

            RiwayatBerhentiTendik.objects.create(
                tendik=t,
                alasan='PENSIUN',
                tanggal=t.tmt_pensiun,
                keterangan='Dibuat otomatis oleh sistem (mencapai TMT Pensiun).',
            )
            total_diproses += 1
            self.stdout.write(f"  → {t.nama_lengkap} (TMT Pensiun: {t.tmt_pensiun})")

        self.stdout.write(self.style.SUCCESS(
            f"Selesai. {total_diproses} tendik diproses pensiun, {total_dilewati} dilewati (sudah tercatat sebelumnya)."
        ))