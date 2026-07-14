"""
Management Command: import_tendik
===================================
Mengimpor data Tenaga Kependidikan dari file gabungan DATA_TENDIK_ALL.xlsx
(Sheet1, data mulai baris ke-4 / index 3)

Struktur kolom (0-based):
  0  NIP
  1  KODE UNIT KERJA
  2  STATUS (PNS / PPPK)
  3  L/P
  4  PANGKAT
  5  GOL.
  6  TMT golongan
  7  JENIS JABATAN
  8  NAMA JABATAN
  9  NAMA DAN JENJANG JABATAN
  10 JENJANG
  11 TMT JABATAN
  12 ANGKA KREDIT
  13-20 MASA KERJA (diabaikan — sudah @property di model)
  21 TMT CPNS
  22 TMT PNS
  23 NAMA TERANG
  24 GELAR DEPAN
  25 GELAR BELAKANG
  26 NO. KTP
  27 AGAMA
  28 TINGKAT IJAZAH BKN
  29 PROFESI (bool)
  30 TEMPAT LAHIR
  31 TANGGAL LAHIR
  32 S1 UNIVERSITAS | 33 S1 FAKULTAS | 34 S1 PRODI | 35 S1 LULUS
  36 S2 UNIVERSITAS | 37 S2 FAKULTAS | 38 S2 PRODI | 39 S2 LULUS
  40 S3 UNIVERSITAS | 41 S3 FAKULTAS | 42 S3 PRODI | 43 S3 LULUS
  44 NIK KTP
  45 NO. HP
  46 EMAIL
  47 ALAMAT
  48 TMT KGB

Penggunaan:
  # Import penuh
  python manage.py import_tendik --file DATA_TENDIK_ALL.xlsx

  # Simulasi tanpa simpan
  python manage.py import_tendik --file DATA_TENDIK_ALL.xlsx --dry-run

  # Update jika NIP sudah ada
  python manage.py import_tendik --file DATA_TENDIK_ALL.xlsx --update

  # Hapus semua lalu import ulang
  python manage.py import_tendik --file DATA_TENDIK_ALL.xlsx --clear --update
"""

from datetime import date, datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

try:
    import pandas as pd
except ImportError:
    raise ImportError("Install pandas: pip install pandas openpyxl")

from tendik.models import (
    UnitKerja, Tendik,
    RiwayatKepangkatanTendik,
    RiwayatJabatanFungsionalTendik,
    JabatanStrukturalTendik,
    RiwayatPendidikanTendik,
)

# ─────────────────────────────────────────────────────────────────────────────
# MAPPING KOLOM
# ─────────────────────────────────────────────────────────────────────────────
C = {
    'nip': 0, 'unit_kode': 1, 'status': 2, 'jk': 3,
    'pangkat': 4, 'golongan': 5, 'tmt_gol': 6,
    'jenis_jabatan': 7, 'nama_jabatan': 8, 'nama_jenjang': 9,
    'jenjang': 10, 'tmt_jabatan': 11, 'angka_kredit': 12,
    # 13-20: masa kerja diabaikan
    'tmt_cpns': 21, 'tmt_pns': 22,
    'nama_terang': 23, 'gelar_depan': 24, 'gelar_belakang': 25,
    'no_ktp': 26, 'agama': 27,
    'ij_bkn': 28, 'ij_profesi': 29,
    'tempat_lahir': 30, 'tanggal_lahir': 31,
    's1_univ': 32, 's1_fak': 33, 's1_prodi': 34, 's1_lulus': 35,
    's2_univ': 36, 's2_fak': 37, 's2_prodi': 38, 's2_lulus': 39,
    's3_univ': 40, 's3_fak': 41, 's3_prodi': 42, 's3_lulus': 43,
    'nik_ktp': 44, 'no_hp': 45, 'email': 46, 'alamat': 47,
    'tmt_kgb': 48,
}

# Normalisasi kode unit kerja (uppercase + alias)
UNIT_ALIAS = {
    'FEB': 'FEKON', 'FAKHUM': 'FAKUM', 'FKEDOK': 'FK',
    'FKESMAS': 'FKM', 'BPK': 'BPKS',
    'RS PENDIDIKAN': 'RS UNTAD',
    'UPA BIMBINGAN KONSELING': 'UPA BK',
    'UPA LABORATORIUM TERPADU': 'UPA LAB TERPADU',
    'UPA PENGEMBANGAN KARIR DAN KEWIRAUSAHAAN': 'UPA PKK',
}

UNIT_NAMA = {
    'BKU': 'Biro Keuangan dan Umum',
    'BAK': 'Biro Akademik dan Kemahasiswaan',
    'BPKS': 'Biro Perencanaan dan Kerjasama',
    'RS UNTAD': 'Rumah Sakit Universitas Tadulako',
    'FKIP': 'Fakultas Keguruan dan Ilmu Pendidikan',
    'PASCASARJANA': 'Pascasarjana',
    'FISIP': 'Fakultas Ilmu Sosial dan Ilmu Politik',
    'FAPERTA': 'Fakultas Pertanian',
    'FEKON': 'Fakultas Ekonomi dan Bisnis',
    'FAPETKAN': 'Fakultas Peternakan dan Perikanan',
    'FKM': 'Fakultas Kesehatan Masyarakat',
    'FMIPA': 'Fakultas Matematika dan Ilmu Pengetahuan Alam',
    'FK': 'Fakultas Kedokteran',
    'FAKUM': 'Fakultas Hukum',
    'LPPM': 'Lembaga Penelitian dan Pengabdian Masyarakat',
    'FAHUT': 'Fakultas Kehutanan',
    'FATEK': 'Fakultas Teknik',
    'UPA BAHASA': 'UPA Bahasa',
    'UPA TIK': 'UPA TIK',
    'LPMPP': 'Lembaga Penjaminan Mutu dan Pengembangan Pembelajaran',
    'UPA LAB TERPADU': 'UPA Laboratorium Terpadu',
    'UPA PKK': 'UPA Pengembangan Karir dan Kewirausahaan',
    'UPA SDHS': 'UPA Sumber Daya Hayati Sulawesi',
    'SATGAS PPKPT': 'Pencegahan dan Penanganan Kekerasan',
    'UPA BK': 'UPA Bimbingan dan Konseling',
    'UPA PERPUSTAKAAN': 'UPA Perpustakaan',
}

UNIT_JENIS = {
    'BKU': 'BIRO', 'BAK': 'BIRO', 'BPKS': 'BIRO',
    'RS UNTAD': 'RS',
    'PASCASARJANA': 'PASCASARJANA',
    'LPPM': 'LEMBAGA', 'LPMPP': 'LEMBAGA',
    'SATGAS PPKPT': 'LAINNYA',
}

JABATAN_FUNGSIONAL_UMUM = {
    'Penata Layanan Operasional', 'Pengelola Umum Operasional',
    'Pengadministrasi Perkantoran', 'Operator Layanan Operasional',
    'Pengemudi', 'Pramu Bakti',
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _s(val):
    if val is None:
        return ''
    s = str(val).strip()
    return '' if s in ('nan', 'NaN', 'None', '-', 'NaT') else s


def _d(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = _s(val)
    if not s:
        return None
    for id_, en in {
        'Januari': 'January', 'Februari': 'February', 'Maret': 'March',
        'April': 'April', 'Mei': 'May', 'Juni': 'June', 'Juli': 'July',
        'Agustus': 'August', 'September': 'September', 'Oktober': 'October',
        'November': 'November', 'Desember': 'December',
    }.items():
        s = s.replace(id_, en)
    for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d %B %Y',
                '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _i(val):
    try:
        v = float(str(val))
        return None if v != v else int(v)
    except (ValueError, TypeError):
        return None


def _f(val):
    try:
        v = float(str(val))
        return None if v != v else v
    except (ValueError, TypeError):
        return None


def _normalize_unit(kode_raw):
    k = _s(kode_raw).upper().strip()
    return UNIT_ALIAS.get(k, k)


def _jenis_unit(kode):
    if kode in UNIT_JENIS:
        return UNIT_JENIS[kode]
    if any(kode.startswith(p) for p in [
        'FKIP', 'FISIP', 'FAPERTA', 'FAPETKAN', 'FEKON',
        'FKM', 'FK', 'FAKUM', 'FAHUT', 'FATEK', 'FMIPA',
    ]):
        return 'FAKULTAS'
    if kode.startswith('UPA'):
        return 'UPA'
    return 'BAGIAN'


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Import data Tendik dari DATA_TENDIK_ALL.xlsx (PNS + PPPK gabungan)'

    def add_arguments(self, parser):
        parser.add_argument('--file',    type=str, required=True,
                            help='Path file Excel DATA_TENDIK_ALL.xlsx')
        parser.add_argument('--dry-run', action='store_true',
                            help='Simulasi tanpa menyimpan ke DB')
        parser.add_argument('--update',  action='store_true',
                            help='Update data jika NIP sudah ada (default: skip)')
        parser.add_argument('--clear',   action='store_true',
                            help='Hapus SEMUA data tendik sebelum import')
        parser.add_argument('--sheet',   type=str, default='Sheet1',
                            help='Nama sheet Excel (default: Sheet1)')

    def handle(self, *args, **options):
        self.dry = options['dry_run']
        self.upd = options['update']

        # Hapus semua jika --clear
        if options['clear'] and not self.dry:
            self.stdout.write(self.style.WARNING('⚠  Menghapus semua data Tendik & UnitKerja...'))
            Tendik.objects.all().delete()
            UnitKerja.objects.all().delete()

        # Baca file Excel
        self.stdout.write(f'📂 Membaca: {options["file"]}')
        try:
            df = pd.read_excel(options['file'], sheet_name=options['sheet'], header=None)
        except FileNotFoundError:
            raise CommandError(f'File tidak ditemukan: {options["file"]}')
        except Exception as e:
            raise CommandError(f'Gagal baca Excel: {e}')

        # Data valid mulai baris index 3, filter yang punya NIP
        data_rows = df.iloc[3:].reset_index(drop=True)
        data_rows = data_rows[data_rows[C['nip']].notna()].reset_index(drop=True)
        total = len(data_rows)
        self.stdout.write(f'   Ditemukan {total} baris ({data_rows[C["status"]].value_counts().to_dict()})\n')

        # Statistik
        self.st = {k: 0 for k in [
            'unit_baru', 'tendik_baru', 'tendik_update', 'tendik_skip',
            'kepangkatan', 'jabfung', 'jabstruk', 'pendidikan', 'error',
        ]}

        with transaction.atomic():
            for idx, row in data_rows.iterrows():
                nip = _s(row[C['nip']])
                if not nip:
                    continue
                try:
                    self._proses(row, nip)
                except Exception as e:
                    self.st['error'] += 1
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ baris {idx+4} NIP={nip}: {e}'
                    ))

            if self.dry:
                self.stdout.write(self.style.WARNING(
                    '\n🔍 DRY-RUN — semua perubahan di-rollback'
                ))
                transaction.set_rollback(True)

        self._ringkasan(total)

    # ── Proses satu baris ─────────────────────────────────────────────────────
    def _proses(self, row, nip):

        # 1. Unit Kerja
        kode = _normalize_unit(row[C['unit_kode']])
        unit = self._get_unit(kode)

        # 2. Cek keberadaan tendik
        existing = Tendik.objects.filter(nip=nip).first()
        if existing and not self.upd:
            self.st['tendik_skip'] += 1
            return

        # 3. Data Tendik
        status = _s(row[C['status']]) or 'PNS'
        no_ktp = _s(row[C['no_ktp']]) or _s(row[C['nik_ktp']])

        payload = dict(
            nama_terang            = _s(row[C['nama_terang']]) or '(Tanpa Nama)',
            gelar_depan            = _s(row[C['gelar_depan']]),
            gelar_belakang         = _s(row[C['gelar_belakang']]),
            jenis_kelamin          = (_s(row[C['jk']]) or 'L')[:1],
            agama                  = _s(row[C['agama']]),
            tempat_lahir           = _s(row[C['tempat_lahir']]),
            tanggal_lahir          = _d(row[C['tanggal_lahir']]),
            no_ktp                 = no_ktp,
            no_hp                  = _s(row[C['no_hp']]),
            email                  = _s(row[C['email']]),
            alamat                 = _s(row[C['alamat']]),
            unit_kerja             = unit,
            status                 = status,
            tmt_cpns               = _d(row[C['tmt_cpns']]),
            tmt_pns                = _d(row[C['tmt_pns']]),
            tmt_kgb                = _d(row[C['tmt_kgb']]),
            tingkat_ijazah_bkn     = _s(row[C['ij_bkn']]),
            tingkat_ijazah_profesi = bool(_s(row[C['ij_profesi']])),
            tingkat_ijazah_borang  = '',
            bidang_keahlian        = '',
            usia_pensiun           = 58 if status == 'PPPK' else 60,
        )

        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            if not self.dry:
                existing.save()
            tendik = existing
            self.st['tendik_update'] += 1
        else:
            tendik = Tendik(nip=nip, **payload)
            if not self.dry:
                tendik.save()
            self.st['tendik_baru'] += 1

        if self.dry:
            return

        # 4. Kepangkatan
        golongan = _s(row[C['golongan']])
        tmt_gol  = _d(row[C['tmt_gol']])
        if golongan and tmt_gol:
            _, created = RiwayatKepangkatanTendik.objects.get_or_create(
                tendik=tendik,
                golongan=golongan,
                tmt=tmt_gol,
                defaults={'pangkat': _s(row[C['pangkat']])},
            )
            if created:
                self.st['kepangkatan'] += 1

        # 5. Jabatan
        jenis_jab = _s(row[C['jenis_jabatan']])
        nama_jab  = _s(row[C['nama_jabatan']])
        jenjang   = _s(row[C['jenjang']]).strip()
        tmt_jab   = _d(row[C['tmt_jabatan']])
        ak        = _f(row[C['angka_kredit']])

        if nama_jab:
            fallback_tmt = date(2024, 1, 1) if status == 'PPPK' else date(2000, 1, 1)

            if 'Fungsional' in jenis_jab or status == 'PPPK':
                jenis_kode = (
                    'FUNGSIONAL_UMUM'
                    if nama_jab in JABATAN_FUNGSIONAL_UMUM
                    else 'FUNGSIONAL_TERTENTU'
                )
                _, created = RiwayatJabatanFungsionalTendik.objects.get_or_create(
                    tendik=tendik,
                    nama_jabatan=nama_jab,
                    tmt=tmt_jab or fallback_tmt,
                    defaults={
                        'jenis': jenis_kode,
                        'jenjang': jenjang,
                        'angka_kredit': ak,
                    },
                )
                if created:
                    self.st['jabfung'] += 1

            elif 'Struktural' in jenis_jab:
                _, created = JabatanStrukturalTendik.objects.get_or_create(
                    tendik=tendik,
                    jabatan=nama_jab,
                    tmt_jabatan=tmt_jab,
                    defaults={'jenjang': jenjang, 'is_aktif': True},
                )
                if created:
                    self.st['jabstruk'] += 1

        # 6. Pendidikan
        for jenjang_pd, cols in [
            ('S1', (C['s1_univ'], C['s1_fak'], C['s1_prodi'], C['s1_lulus'])),
            ('S2', (C['s2_univ'], C['s2_fak'], C['s2_prodi'], C['s2_lulus'])),
            ('S3', (C['s3_univ'], C['s3_fak'], C['s3_prodi'], C['s3_lulus'])),
        ]:
            univ  = _s(row[cols[0]])
            fak   = _s(row[cols[1]])
            prodi = _s(row[cols[2]])
            lulus = _i(row[cols[3]])
            if univ or prodi:
                _, created = RiwayatPendidikanTendik.objects.get_or_create(
                    tendik=tendik,
                    jenjang=jenjang_pd,
                    defaults={
                        'institusi': univ, 'fakultas_pt': fak,
                        'bidang_studi': prodi, 'tahun_lulus': lulus,
                    },
                )
                if created:
                    self.st['pendidikan'] += 1

    # ── Get/Create UnitKerja ──────────────────────────────────────────────────
    def _get_unit(self, kode):
        if not kode:
            return None
        if self.dry:
            return UnitKerja(kode=kode, nama=UNIT_NAMA.get(kode, kode))
        obj, created = UnitKerja.objects.get_or_create(
            kode=kode,
            defaults={
                'nama':  UNIT_NAMA.get(kode, kode),
                'jenis': _jenis_unit(kode),
            }
        )
        if created:
            self.st['unit_baru'] += 1
        return obj

    # ── Ringkasan ─────────────────────────────────────────────────────────────
    def _ringkasan(self, total):
        s = self.st
        mode = '🔍 DRY-RUN' if self.dry else '✅ SELESAI'
        garis = '═' * 46
        self.stdout.write(f'\n{garis}')
        self.stdout.write(self.style.SUCCESS(f' {mode} — Ringkasan Import Tendik'))
        self.stdout.write(garis)
        self.stdout.write(f'  Total baris diproses   : {total}')
        self.stdout.write(f'  Unit Kerja baru        : {s["unit_baru"]}')
        self.stdout.write(f'  Tendik baru            : {s["tendik_baru"]}')
        self.stdout.write(f'  Tendik diupdate        : {s["tendik_update"]}')
        self.stdout.write(f'  Tendik diskip          : {s["tendik_skip"]}')
        self.stdout.write(f'  Kepangkatan            : {s["kepangkatan"]}')
        self.stdout.write(f'  Jabatan Fungsional     : {s["jabfung"]}')
        self.stdout.write(f'  Jabatan Struktural     : {s["jabstruk"]}')
        self.stdout.write(f'  Riwayat Pendidikan     : {s["pendidikan"]}')
        if s['error']:
            self.stdout.write(self.style.ERROR(
                f'  Error                  : {s["error"]} (lihat log di atas)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('  Error                  : 0 ✓'))
        self.stdout.write(f'{garis}\n')