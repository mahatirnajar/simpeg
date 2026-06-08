"""
Management command: import_duk
Usage: python manage.py import_duk <path_to_xlsx>

Mengimpor data dari file DUK Excel ke database Django.
Kolom Excel (berdasarkan file DUK_PNS_2026.xlsx):
0:NO, 1:NIDN, 2:NUPTK, 3:NIP, 4:NAMA_DOSEN, 5:KODE_FAK, 6:NAMA_FAK,
7:STATUS, 8:LP, 9:PANGKAT, 10:GOLONGAN, 11:TMT_PANGKAT,
12:JENJANG_JAB, 13:TMT_JAB, 14:AK_KUM,
15-24: MASA KERJA (cpns thn/bln, gol thn/bln, jab thn/bln, keseluruhan thn/bln, pensiun thn/bln)
25:JURUSAN, 26:JENJANG_PRODI, 27:PRODI, 28:NO_REG_SERDOS, 29:NIRA, 30:KARPEG,
31:TMT_CPNS, 32:TMT_PNS, 33:NAMA_TERANG, 34:GELAR_DEPAN, 35:GELAR_BELAKANG,
36:NO_KTP, 37:AGAMA, 38:KEPAKARAN,
39:TUGAS_JAB, 40:NO_SK, 41:TGL_SK, 42:TMT_JABATAN_TAM,
43:IJ_BKN, 44:IJ_BORANG, 45:TEMPAT_LAHIR, 46:TGL_LAHIR, 47:blank, 48:USIA, 49:USIA_PENSIUN, 50:TAHUN_PENSIUN
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import openpyxl
from datetime import datetime, date


class Command(BaseCommand):
    help = 'Import data DUK dosen dari file Excel'

    def add_arguments(self, parser):
        parser.add_argument('xlsx_path', type=str, help='Path ke file Excel DUK')

    def handle(self, *args, **options):
        from dosen.models import Dosen, Fakultas, RiwayatKepangkatan, RiwayatJabatanFungsional, TugasTambahan, MasaKerja

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
                # Excel serial date
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
            if val is None:
                return ''
            return str(val).strip()

        def clean_int(val):
            if val is None:
                return None
            try:
                return int(float(str(val)))
            except:
                return None

        def clean_decimal(val):
            if val is None:
                return None
            try:
                return float(str(val))
            except:
                return None

        imported = 0
        skipped = 0
        errors = 0

        for row_idx, row in enumerate(ws.iter_rows(min_row=5, values_only=True)):
            # Skip header rows and empty rows
            if not row or row[0] is None:
                continue
            try:
                no = clean_int(row[0])
                if not no:
                    continue
            except:
                continue

            try:
                vals = list(row)
                # Pad to length 55
                while len(vals) < 55:
                    vals.append(None)

                nidn = clean(vals[1]) or None
                nuptk = clean(vals[2]) or None
                nip = clean(vals[3]) or None
                nama_lengkap = clean(vals[4])
                kode_fak = clean(vals[5])
                nama_fak = clean(vals[6])
                status = clean(vals[7]) or 'PNS'
                jk = clean(vals[8]) or 'L'
                pangkat = clean(vals[9])
                golongan = clean(vals[10])
                tmt_pangkat = parse_date(vals[11])
                jenjang_jab = clean(vals[12])
                tmt_jab = parse_date(vals[13])
                ak_kum = clean_decimal(vals[14])
                # Masa kerja: cols 15-24
                mk_cpns_thn = clean_int(vals[15])
                mk_cpns_bln = clean_int(vals[16])
                mk_gol_thn = clean_int(vals[17])
                mk_gol_bln = clean_int(vals[18])
                mk_jab_thn = clean_int(vals[19])
                mk_jab_bln = clean_int(vals[20])
                mk_kes_thn = clean_int(vals[21])
                mk_kes_bln = clean_int(vals[22])
                mk_pen_thn = clean_int(vals[23])
                mk_pen_bln = clean_int(vals[24])

                jurusan = clean(vals[25])
                jenjang_prodi = clean(vals[26])
                prodi = clean(vals[27])
                no_reg_serdos = clean(vals[28]) or None
                nira = clean(vals[29]) or None
                karpeg = clean(vals[30]) or None
                tmt_cpns = parse_date(vals[31])
                tmt_pns = parse_date(vals[32])
                nama_terang = clean(vals[33])
                gelar_depan = clean(vals[34])
                gelar_belakang = clean(vals[35])
                no_ktp = clean(vals[36]) or None
                agama = clean(vals[37])
                kepakaran = clean(vals[38])
                tugas_jab = clean(vals[39])
                no_sk = clean(vals[40])
                tgl_sk = parse_date(vals[41])
                tmt_jab_tam = parse_date(vals[42])
                ij_bkn = clean(vals[43])
                ij_borang = clean(vals[44])
                tempat_lahir = clean(vals[45])
                tgl_lahir_raw = vals[46]
                tgl_lahir = parse_date(tgl_lahir_raw)
                usia_pensiun = clean_int(vals[48]) if len(vals) > 48 else None
                tahun_pensiun = clean_int(vals[49]) if len(vals) > 49 else None

                if not nama_lengkap:
                    skipped += 1
                    continue

                # Get or create Fakultas
                fak = None
                if kode_fak:
                    fak, _ = Fakultas.objects.get_or_create(
                        kode=kode_fak,
                        defaults={'nama': nama_fak or kode_fak}
                    )

                # Agama validation
                valid_agama = ['Islam', 'Kristen', 'Katolik', 'Hindu', 'Budha', 'Konghucu']
                if agama not in valid_agama:
                    agama = ''

                # Create or update Dosen
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
                    'nidn': nidn,
                    'nuptk': nuptk,
                    'no_ktp': no_ktp,
                    'karpeg': karpeg,
                    'nira': nira,
                    'no_reg_serdos': no_reg_serdos,
                    'jenis_kelamin': jk if jk in ['L', 'P'] else 'L',
                    'agama': agama,
                    'tempat_lahir': tempat_lahir,
                    'tanggal_lahir': tgl_lahir,
                    'fakultas': fak,
                    'jurusan_bagian': jurusan,
                    'program_studi_nama': prodi,
                    'jenjang_prodi': jenjang_prodi,
                    'status': status if status in ['PNS', 'CPNS', 'PPPK', 'Non-PNS'] else 'PNS',
                    'tmt_cpns': tmt_cpns,
                    'tmt_pns': tmt_pns,
                    'ranting_ilmu': kepakaran,
                    'tingkat_ijazah_bkn': ij_bkn,
                    'tingkat_ijazah_borang': ij_borang,
                    'usia_pensiun': usia_pensiun,
                    'tahun_pensiun': tahun_pensiun,
                    'created_by': admin_user,
                }
                if nip:
                    defaults.pop('nip', None)

                dosen, created = Dosen.objects.update_or_create(**lookup, defaults=defaults)

                # Riwayat Kepangkatan
                if pangkat and golongan and tmt_pangkat:
                    RiwayatKepangkatan.objects.get_or_create(
                        dosen=dosen, pangkat=pangkat, golongan=golongan, tmt=tmt_pangkat
                    )

                # Riwayat Jabatan Fungsional
                if jenjang_jab and tmt_jab:
                    RiwayatJabatanFungsional.objects.get_or_create(
                        dosen=dosen, jenjang=jenjang_jab, tmt=tmt_jab,
                        defaults={'angka_kredit': ak_kum}
                    )

                # Tugas Tambahan
                if tugas_jab:
                    TugasTambahan.objects.get_or_create(
                        dosen=dosen, jabatan=tugas_jab,
                        defaults={'no_sk': no_sk, 'tgl_sk': tgl_sk, 'tmt_jabatan': tmt_jab_tam, 'is_aktif': True}
                    )

                # Masa Kerja
                MasaKerja.objects.update_or_create(
                    dosen=dosen,
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
                    self.stdout.write(f'  {imported} dosen diproses...')

            except Exception as e:
                errors += 1
                self.stderr.write(f'  Error baris {row_idx+5}: {e}')
                continue

        wb.close()
        self.stdout.write(self.style.SUCCESS(
            f'\nSelesai! {imported} dosen berhasil diimport, {skipped} dilewati, {errors} error.'
        ))
