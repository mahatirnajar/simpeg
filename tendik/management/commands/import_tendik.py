"""
Management command: import_tendik
Usage: python manage.py import_tendik <path_to_xlsx>

Import data Tendik dari file Excel berformat DUK.
Kolom Excel sama persis dengan DUK Dosen (sesuai permintaan user):
0:NO, 1:NIDN/NI, 2:NUPTK, 3:NIP, 4:NAMA, 5:KODE_UNIT, 6:NAMA_UNIT,
7:STATUS, 8:LP, 9:PANGKAT, 10:GOL, 11:TMT_PANGKAT,
12:JENJANG_JAB_FUNGSIONAL, 13:TMT_JAB, 14:AK_KUM,
15-24: MASA KERJA (cpns thn/bln, gol thn/bln, jab thn/bln, keseluruhan thn/bln, pensiun thn/bln)
25:BAGIAN, 26:blank, 27:blank, 28:blank, 29:NIRA, 30:KARPEG,
31:TMT_CPNS, 32:TMT_PNS, 33:NAMA_TERANG, 34:GELAR_DEPAN, 35:GELAR_BELAKANG,
36:NO_KTP, 37:AGAMA, 38:BIDANG_KEAHLIAN,
39:TUGAS_JAB, 40:NO_SK, 41:TGL_SK, 42:TMT_JAB_TAM,
43:IJ_BKN, 44:IJ_BORANG, 45:TEMPAT_LAHIR, 46:TGL_LAHIR,
47:blank, 48:USIA, 49:USIA_PENSIUN, 50:TAHUN_PENSIUN
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import openpyxl
from datetime import datetime, date


class Command(BaseCommand):
    help = 'Import data DUK tendik dari file Excel'

    def add_arguments(self, parser):
        parser.add_argument('xlsx_path', type=str, help='Path ke file Excel DUK Tendik')

    def handle(self, *args, **options):
        from tendik.models import (
            Tendik, UnitKerja,
            RiwayatKepangkatanTendik, RiwayatJabatanFungsionalTendik,
            JabatanStrukturalTendik, TugasTambahanTendik, MasaKerjaTendik,
        )
        from dosen.models import Fakultas

        path = options['xlsx_path']
        self.stdout.write(f'Membuka file: {path}')

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        admin_user = User.objects.filter(is_superuser=True).first()

        def parse_date(val):
            if val is None:
                return None
            if isinstance(val, (datetime, date)):
                return val if isinstance(val, date) else val.date()
            if isinstance(val, (int, float)):
                try:
                    from openpyxl.utils.datetime import from_excel
                    return from_excel(int(val))
                except:
                    return None
            if isinstance(val, str):
                for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        return datetime.strptime(val.strip(), fmt).date()
                    except:
                        pass
            return None

        def clean(val):
            return str(val).strip() if val is not None else ''

        def clean_int(val):
            try:
                return int(float(str(val))) if val is not None else None
            except:
                return None

        def clean_decimal(val):
            try:
                return float(str(val)) if val is not None else None
            except:
                return None

        imported = skipped = errors = 0

        for row_idx, row in enumerate(ws.iter_rows(min_row=5, values_only=True)):
            if not row or row[0] is None:
                continue
            try:
                no = clean_int(row[0])
                if not no:
                    continue
            except:
                continue

            try:
                v = list(row)
                while len(v) < 55:
                    v.append(None)

                nidn         = clean(v[1]) or None
                nuptk        = clean(v[2]) or None
                nip          = clean(v[3]) or None
                nama_lengkap = clean(v[4])
                kode_unit    = clean(v[5])
                nama_unit    = clean(v[6])
                status       = clean(v[7]) or 'PNS'
                jk           = clean(v[8]) or 'L'
                pangkat      = clean(v[9])
                golongan     = clean(v[10])
                tmt_pangkat  = parse_date(v[11])
                jenjang_jab  = clean(v[12])
                tmt_jab      = parse_date(v[13])
                ak_kum       = clean_decimal(v[14])

                mk_cpns_thn = clean_int(v[15]); mk_cpns_bln = clean_int(v[16])
                mk_gol_thn  = clean_int(v[17]); mk_gol_bln  = clean_int(v[18])
                mk_jab_thn  = clean_int(v[19]); mk_jab_bln  = clean_int(v[20])
                mk_kes_thn  = clean_int(v[21]); mk_kes_bln  = clean_int(v[22])
                mk_pen_thn  = clean_int(v[23]); mk_pen_bln  = clean_int(v[24])

                bagian       = clean(v[25])
                nira         = clean(v[29]) or None
                karpeg       = clean(v[30]) or None
                tmt_cpns     = parse_date(v[31])
                tmt_pns      = parse_date(v[32])
                nama_terang  = clean(v[33])
                gelar_depan  = clean(v[34])
                gelar_belakang = clean(v[35])
                no_ktp       = clean(v[36]) or None
                agama        = clean(v[37])
                kepakaran    = clean(v[38])
                tugas_jab    = clean(v[39])
                no_sk        = clean(v[40])
                tgl_sk       = parse_date(v[41])
                tmt_jab_tam  = parse_date(v[42])
                ij_bkn       = clean(v[43])
                ij_borang    = clean(v[44])
                tempat_lahir = clean(v[45])
                tgl_lahir    = parse_date(v[46])
                usia_pensiun = clean_int(v[48]) if len(v) > 48 else None
                tahun_pensiun = clean_int(v[49]) if len(v) > 49 else None

                if not nama_lengkap:
                    skipped += 1
                    continue

                # Unit kerja - buat sebagai UnitKerja (bukan Fakultas)
                unit = None
                if kode_unit:
                    unit, _ = UnitKerja.objects.get_or_create(
                        kode=kode_unit,
                        defaults={'nama': nama_unit or kode_unit, 'jenis': 'LAINNYA'}
                    )

                valid_agama = ['Islam', 'Kristen', 'Katolik', 'Hindu', 'Budha', 'Konghucu']
                if agama not in valid_agama:
                    agama = ''

                lookup = {}
                if nip:
                    lookup['nip'] = nip
                elif nidn:
                    lookup['nidn'] = nidn
                else:
                    lookup['nama_lengkap'] = nama_lengkap

                defaults = {
                    'nama_lengkap': nama_lengkap,
                    'nama_terang': nama_terang or nama_lengkap,
                    'gelar_depan': gelar_depan,
                    'gelar_belakang': gelar_belakang,
                    'nidn': nidn, 'nuptk': nuptk,
                    'no_ktp': no_ktp, 'karpeg': karpeg, 'nira': nira,
                    'jenis_kelamin': jk if jk in ['L', 'P'] else 'L',
                    'agama': agama,
                    'tempat_lahir': tempat_lahir,
                    'tanggal_lahir': tgl_lahir,
                    'unit_kerja': unit,
                    'bagian': bagian,
                    'status': status if status in ['PNS', 'CPNS', 'PPPK', 'Non-PNS'] else 'PNS',
                    'tmt_cpns': tmt_cpns, 'tmt_pns': tmt_pns,
                    'bidang_keahlian': kepakaran,
                    'tingkat_ijazah_bkn': ij_bkn,
                    'tingkat_ijazah_borang': ij_borang,
                    'usia_pensiun': usia_pensiun,
                    'tahun_pensiun': tahun_pensiun,
                    'created_by': admin_user,
                }

                tendik, created = Tendik.objects.update_or_create(**lookup, defaults=defaults)

                if pangkat and golongan and tmt_pangkat:
                    RiwayatKepangkatanTendik.objects.get_or_create(
                        tendik=tendik, pangkat=pangkat, golongan=golongan, tmt=tmt_pangkat
                    )

                if jenjang_jab and tmt_jab:
                    RiwayatJabatanFungsionalTendik.objects.get_or_create(
                        tendik=tendik, jenjang=jenjang_jab, tmt=tmt_jab,
                        defaults={'angka_kredit': ak_kum}
                    )

                if tugas_jab:
                    TugasTambahanTendik.objects.get_or_create(
                        tendik=tendik, jabatan=tugas_jab,
                        defaults={'no_sk': no_sk, 'tgl_sk': tgl_sk, 'tmt_jabatan': tmt_jab_tam, 'is_aktif': True}
                    )

                MasaKerjaTendik.objects.update_or_create(
                    tendik=tendik,
                    defaults={
                        'cpns_tahun': mk_cpns_thn, 'cpns_bulan': mk_cpns_bln,
                        'golongan_tahun': mk_gol_thn, 'golongan_bulan': mk_gol_bln,
                        'jabatan_tahun': mk_jab_thn, 'jabatan_bulan': mk_jab_bln,
                        'keseluruhan_tahun': mk_kes_thn, 'keseluruhan_bulan': mk_kes_bln,
                        'pensiun_tahun': mk_pen_thn, 'pensiun_bulan': mk_pen_bln,
                    }
                )

                imported += 1
                if imported % 50 == 0:
                    self.stdout.write(f'  {imported} tendik diproses...')

            except Exception as e:
                errors += 1
                self.stderr.write(f'  Error baris {row_idx+5}: {e}')
                continue

        wb.close()
        self.stdout.write(self.style.SUCCESS(
            f'\nSelesai! {imported} tendik berhasil diimport, {skipped} dilewati, {errors} error.'
        ))
