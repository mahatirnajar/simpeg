from django.core.management.base import BaseCommand
from django.utils import timezone
from dosen.models import Dosen, RiwayatStatusDosen


STATUS_TIDAK_AKTIF = ['PENSIUN', 'MENINGGAL', 'BERHENTI', 'PINDAH']


class Command(BaseCommand):
    help = "Proses otomatis dosen yang mencapai TMT Pensiun (BUP) — pindahkan dari Dashboard ke Dosen Berhenti"

    def handle(self, *args, **options):
        today = timezone.localdate()

        dosen_qs = Dosen.objects.filter(
            tmt_pensiun__isnull=False,
            tmt_pensiun__lte=today,
        ).prefetch_related('riwayat_status')

        total_diproses = 0
        total_dilewati = 0

        for dosen in dosen_qs:
            status_terakhir = dosen.status_terakhir

            # Lewati jika dosen sudah punya status tidak aktif (sudah pernah diproses)
            if status_terakhir and status_terakhir.status in STATUS_TIDAK_AKTIF:
                total_dilewati += 1
                continue

            RiwayatStatusDosen.objects.create(
                dosen=dosen,
                status='PENSIUN',
                tanggal_mulai=dosen.tmt_pensiun,
                keterangan='Dibuat otomatis oleh sistem (mencapai Batas Usia Pensiun).',
            )
            total_diproses += 1
            self.stdout.write(f"  → {dosen.nama_lengkap} (TMT Pensiun: {dosen.tmt_pensiun})")

        self.stdout.write(self.style.SUCCESS(
            f"Selesai. {total_diproses} dosen diproses pensiun, {total_dilewati} dilewati (sudah tercatat sebelumnya)."
        ))