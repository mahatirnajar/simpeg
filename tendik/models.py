from datetime import date
from typing import Optional, Tuple
from dateutil.relativedelta import relativedelta
from django.db import models
from django.contrib.auth.models import User


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _selisih_tahun_bulan(dari: date, sampai: date) -> Tuple[int, int]:
    """Kembalikan (tahun, bulan) selisih antara dua tanggal."""
    if dari is None or sampai is None:
        return (0, 0)
    r = relativedelta(sampai, dari)
    return (r.years, r.months)


# ─────────────────────────────────────────────────────────────────────────────
# REFERENSI
# ─────────────────────────────────────────────────────────────────────────────

class UnitKerja(models.Model):
    kode  = models.CharField(max_length=20, unique=True)
    nama  = models.CharField(max_length=200)
    class Meta:
        verbose_name = "Unit Kerja"
        verbose_name_plural = "Unit Kerja"
        ordering = ['nama']

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class ReferensiJabatan(models.Model):
    """
    Master jabatan: nama, kelas jabatan, dan nominal gaji (khusus PPPK).
    Sumber: sheet harga_jabatan_tendik di file PPPK.
    """
    JENIS_CHOICES = [
        ('STRUKTURAL',          'Struktural'),
        ('FUNGSIONAL_TERTENTU', 'Fungsional Tertentu'),
        ('FUNGSIONAL_UMUM',     'Fungsional Umum / Pelaksana'),
    ]
    jenis         = models.CharField(max_length=30, choices=JENIS_CHOICES)
    nama_jabatan  = models.CharField(max_length=200)
    id_grade      = models.IntegerField(null=True, blank=True, verbose_name="ID Grade (PPPK)")
    kelas_jabatan = models.IntegerField(null=True, blank=True)
    nominal_gaji  = models.BigIntegerField(null=True, blank=True, verbose_name="Nominal Gaji (Rp)")

    class Meta:
        verbose_name = "Referensi Jabatan"
        unique_together = [('jenis', 'nama_jabatan')]
        ordering = ['jenis', 'nama_jabatan']

    def __str__(self):
        return f"[{self.get_jenis_display()}] {self.nama_jabatan}"


# ─────────────────────────────────────────────────────────────────────────────
# MODEL UTAMA TENDIK
# ─────────────────────────────────────────────────────────────────────────────

class Tendik(models.Model):
    JENIS_KELAMIN_CHOICES = [('L', 'Laki-laki'), ('P', 'Perempuan')]
    AGAMA_CHOICES = [
        ('Islam',    'Islam'), ('Kristen', 'Kristen'), ('Katolik', 'Katolik'),
        ('Hindu',    'Hindu'), ('Budha',   'Budha'),   ('Konghucu','Konghucu'),
    ]
    STATUS_CHOICES = [
        ('PNS', 'PNS'), ('CPNS', 'CPNS'), ('PPPK', 'PPPK'), ('PTT', 'PTT'),
    ]
    TINGKAT_IJAZAH_CHOICES = [
        ('SD','SD'), ('SLTP','SLTP'), ('SLTA','SLTA'),
        ('D3','D3'), ('D4','D4'), ('S1','S1'), ('S2','S2'), ('S3','S3'),
        ('PROFESI','Profesi'),
    ]

    # ── Identitas ─────────────────────────────────────────────────────────────
    nuptk  = models.CharField(max_length=30,  null=True, blank=True, verbose_name="NUPTK")
    nip    = models.CharField(max_length=30,  unique=True, null=True, blank=True, verbose_name="NIP")
    no_ktp = models.CharField(max_length=20,  null=True, blank=True, verbose_name="No. KTP / NIK")

    # ── Nama — DATA PRIMER ────────────────────────────────────────────────────
    nama_terang    = models.CharField(max_length=200, verbose_name="Nama Terang (tanpa gelar)")
    gelar_depan    = models.CharField(max_length=100, blank=True, verbose_name="Gelar Depan")
    gelar_belakang = models.CharField(max_length=100, blank=True, verbose_name="Gelar Belakang")

    # ── Data Pribadi ──────────────────────────────────────────────────────────
    jenis_kelamin = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES)
    agama         = models.CharField(max_length=20, choices=AGAMA_CHOICES, blank=True)
    tempat_lahir  = models.CharField(max_length=100, blank=True)
    tanggal_lahir = models.DateField(null=True, blank=True)

    # ── Kontak ────────────────────────────────────────────────────────────────
    no_hp  = models.CharField(max_length=20, blank=True, verbose_name="No. HP")
    email  = models.EmailField(blank=True)
    alamat = models.TextField(blank=True)

    unit_kerja = models.ForeignKey(
        UnitKerja,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tendik',
        verbose_name="Unit Kerja"
    )

    bagian = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Bagian/Sub-Bagian"
    )

    # ── Status Kepegawaian ────────────────────────────────────────────────────
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PNS')
    tmt_pns  = models.DateField(null=True, blank=True, verbose_name="TMT PNS")
    
    # MASA KERJA CPNS DIAKUI
    mk_cpns_tahun = models.IntegerField(null=True, blank=True, verbose_name="Masa Kerja CPNS (Tahun)")
    mk_cpns_bulan = models.IntegerField(null=True, blank=True, verbose_name="Masa Kerja CPNS (Bulan)")

    # ── Pendidikan ────────────────────────────────────────────────────────────
    bidang_keahlian        = models.CharField(max_length=300, blank=True, verbose_name="Ranting Ilmu / Kepakaran")
    tingkat_ijazah_bkn     = models.CharField(max_length=10, blank=True, choices=TINGKAT_IJAZAH_CHOICES, verbose_name="Tingkat Ijazah BKN")
    tingkat_ijazah_profesi = models.BooleanField(default=False, verbose_name="Memiliki Ijazah Profesi")
    tingkat_ijazah_borang  = models.CharField(max_length=10, blank=True, verbose_name="Tingkat Ijazah Borang")


    usia_pensiun = models.IntegerField(null=True, blank=True, default=58, verbose_name="Usia Pensiun")
    tmt_pensiun  = models.DateField(null=True, blank=True, verbose_name="TMT Pensiun")

    # ── KGB ───────────────────────────────────────────────────────────────────
    tmt_kgb = models.DateField(null=True, blank=True, verbose_name="TMT Kenaikan Gaji Berkala")

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='tendik_created'
    )

    class Meta:
        ordering = ['nama_terang']
        verbose_name = "Tenaga Kependidikan"
        verbose_name_plural = "Tenaga Kependidikan"

    def __str__(self):
        return self.nama_lengkap

    # ═════════════════════════════════════════════════════════════════════════
    # PROPERTIES — dihitung otomatis, TIDAK disimpan di DB
    # ═════════════════════════════════════════════════════════════════════════

    # ── Nama ──────────────────────────────────────────────────────────────────
    @property
    def nama_lengkap(self):
        """
        Rumus: gelar_depan + nama_terang + gelar_belakang
        Contoh:
          "Dr."  + "Elvia Alhusni" + "S.Si., M.Sc." → "Dr. Elvia Alhusni, S.Si., M.Sc."
          ""     + "Kamelia Burhan" + "S.E., M.M."   → "Kamelia Burhan, S.E., M.M."
          "Drs." + "I Gede Surata" + "M.Si."         → "Drs. I Gede Surata, M.Si."
        """
        nama = self.nama_terang.strip()
        if self.gelar_belakang:
            nama = nama + ', ' + self.gelar_belakang.strip()
        if self.gelar_depan:
            nama = self.gelar_depan.strip() + ' ' + nama
        return nama

    # ── Unit ──────────────────────────────────────────────────────────────────
    @property
    def nama_unit(self):
        if self.unit_kerja:
            return self.unit_kerja.nama
        return '-'

    # ── Usia ──────────────────────────────────────────────────────────────────
    @property
    def usia_saat_ini(self):
        """Rumus Excel: =DATEDIF(tgl_lahir, TODAY(), "Y")"""
        if not self.tanggal_lahir:
            return None
        today = date.today()
        return today.year - self.tanggal_lahir.year - (
            (today.month, today.day) < (self.tanggal_lahir.month, self.tanggal_lahir.day)
        )

    # ── Pensiun ───────────────────────────────────────────────────────────────
    def hitung_tmt_pensiun(self):
        """
        Rumus Excel: tanggal 1 bulan berikutnya setelah HUT ke-usia_pensiun.
        Contoh: lahir 02-04-1974, pensiun 58 → 01-05-2032
                lahir 15-12-1968, pensiun 58 → 01-01-2027
        Tidak menyimpan ke DB — hanya menghitung nilai yang seharusnya.
        """
        if not self.tanggal_lahir or not self.usia_pensiun:
            return None
        tgl = self.tanggal_lahir
        tahun_pensiun = tgl.year + self.usia_pensiun
        if tgl.month < 12:
            return date(tahun_pensiun, tgl.month + 1, 1)
        else:
            return date(tahun_pensiun + 1, 1, 1)

    @property
    def tahun_pensiun(self):
        return self.tmt_pensiun.year if self.tmt_pensiun else None

    @property
    def sudah_pensiun(self):
        return bool(self.tmt_pensiun and self.tmt_pensiun <= date.today())

    def save(self, *args, **kwargs):
        # Auto-hitung tmt_pensiun HANYA jika masih kosong (tendik baru / belum diisi manual).
        # Jika admin sudah mengubahnya manual, nilai itu tidak akan ditimpa lagi.
        if not self.tmt_pensiun:
            self.tmt_pensiun = self.hitung_tmt_pensiun()
        super().save(*args, **kwargs)

    # TMT CPNS
    @property
    def tmt_cpns(self):
        if not self.nip or len(self.nip) < 14:
            return None

        try:
            tahun = int(self.nip[8:12])
            bulan = int(self.nip[12:14])

            return date(tahun, bulan, 1)
        except (ValueError, TypeError):
            return None
    # ── Masa Kerja ────────────────────────────────────────────────────────────
    @property
    def masa_kerja_golongan(self):
        """(tahun, bulan) sejak TMT kepangkatan terakhir hingga hari ini."""
        kpk = self.kepangkatan_terakhir
        if kpk and kpk.tmt:
            return _selisih_tahun_bulan(kpk.tmt, date.today())
        return (0, 0)

    @property
    def masa_kerja_jabatan(self):
        """(tahun, bulan) sejak TMT jabatan aktif terakhir hingga hari ini."""
        jab_f = self.jabatan_fungsional_terakhir
        jab_s = self.jabatan_struktural_aktif
        tmt = None
        if jab_f:
            tmt = jab_f.tmt
        elif jab_s:
            tmt = jab_s.tmt_jabatan
        if tmt:
            return _selisih_tahun_bulan(tmt, date.today())
        return (0, 0)

    @property
    def masa_kerja_keseluruhan(self):

        tmt_cpns = self.tmt_cpns
        if not tmt_cpns:
            return (0, 0)

        tahun = getattr(self, 'mk_cpns_tahun', 0) or 0
        bulan = getattr(self, 'mk_cpns_bulan', 0) or 0

        tmt_awal = tmt_cpns - relativedelta(
            years=tahun,
            months=bulan
        )

        return _selisih_tahun_bulan(tmt_awal, date.today())

    @property
    def masa_kerja_pensiun(self):
        """(tahun, bulan) SISA masa kerja hingga TMT pensiun."""
        if self.tmt_pensiun and self.tmt_pensiun > date.today():
            return _selisih_tahun_bulan(date.today(), self.tmt_pensiun)
        return (0, 0)

    @property
    def sisa_masa_kerja_str(self):
        """Format teks untuk kolom DUK: '23 Thn, 11 Bln'."""
        t, b = self.masa_kerja_pensiun
        if t == 0 and b == 0:
            return 'Sudah Pensiun'
        return f"{t} Thn, {b} Bln"

    # ── Shortcut ke relasi ────────────────────────────────────────────────────
    @property
    def kepangkatan_terakhir(self):
        return self.riwayat_kepangkatan.order_by('-tmt').first()

    @property
    def jabatan_fungsional_terakhir(self):
        return self.riwayat_jabatan_fungsional.order_by('-tmt').first()

    @property
    def jabatan_struktural_aktif(self):
        return self.jabatan_struktural.filter(is_aktif=True).first()

    @property
    def tugas_tambahan_aktif(self):
        return self.tugas_tambahan.filter(is_aktif=True).first()

    @property
    def status_terakhir(self):
        return self.riwayat_status.order_by('-tanggal_mulai').first()


# ─────────────────────────────────────────────────────────────────────────────
# KEPANGKATAN
# ─────────────────────────────────────────────────────────────────────────────

class RiwayatKepangkatanTendik(models.Model):
    """
    PNS : pangkat + golongan romawi (II/a … IV/e)
    PPPK: pangkat kosong, golongan angka romawi (I, V, VII, IX, X, XI)
    """
    tendik     = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='riwayat_kepangkatan')
    pangkat    = models.CharField(max_length=100, blank=True)
    golongan   = models.CharField(max_length=10)
    tmt        = models.DateField()
    keterangan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt']
        verbose_name = "Riwayat Kepangkatan Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} – {self.pangkat} ({self.golongan})"


# ─────────────────────────────────────────────────────────────────────────────
# JABATAN FUNGSIONAL
# ─────────────────────────────────────────────────────────────────────────────

class RiwayatJabatanFungsionalTendik(models.Model):
    JENIS_CHOICES = [
        ('FUNGSIONAL_TERTENTU', 'Fungsional Tertentu'),
        ('FUNGSIONAL_UMUM',     'Fungsional Umum / Pelaksana'),
    ]
    JENJANG_CHOICES = [
        ('Ahli Utama',        'Ahli Utama'),
        ('Ahli Madya',        'Ahli Madya'),
        ('Ahli Muda',         'Ahli Muda'),
        ('Ahli Pertama',      'Ahli Pertama'),
        ('Penyelia',          'Penyelia'),
        ('Mahir',             'Mahir'),
        ('Terampil',          'Terampil'),
        ('Pelaksana Lanjutan','Pelaksana Lanjutan'),
        ('Pelaksana',         'Pelaksana'),
    ]

    tendik       = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='riwayat_jabatan_fungsional')
    jenis        = models.CharField(max_length=30, choices=JENIS_CHOICES, default='FUNGSIONAL_TERTENTU')
    nama_jabatan = models.CharField(max_length=200, blank=True, default='', verbose_name="Nama Jabatan")
    jenjang      = models.CharField(max_length=50, choices=JENJANG_CHOICES, blank=True)
    tmt          = models.DateField()
    angka_kredit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    keterangan   = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt']
        verbose_name = "Riwayat Jabatan Fungsional Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} – {self.nama_jabatan} {self.jenjang}"

    @property
    def nama_dan_jenjang(self):
        """Contoh: 'Pustakawan Ahli Madya'"""
        return f"{self.nama_jabatan} {self.jenjang}".strip()

    @property
    def masa_kerja_jabatan(self):
        """(tahun, bulan) sejak TMT jabatan fungsional ini."""
        return _selisih_tahun_bulan(self.tmt, date.today())


# ─────────────────────────────────────────────────────────────────────────────
# JABATAN STRUKTURAL
# ─────────────────────────────────────────────────────────────────────────────

class JabatanStrukturalTendik(models.Model):
    tendik      = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='jabatan_struktural')
    jabatan     = models.CharField(max_length=200)
    jenjang     = models.CharField(max_length=100, blank=True)
    eselon      = models.CharField(
        max_length=10, blank=True,
        choices=[
            ('II/a','II/a'), ('II/b','II/b'),
            ('III/a','III/a'), ('III/b','III/b'),
            ('IV/a','IV/a'), ('IV/b','IV/b'),
            ('Pelaksana','Pelaksana'),
        ],
        verbose_name="Eselon"
    )
    unit_kerja  = models.CharField(max_length=200, blank=True)
    no_sk       = models.CharField(max_length=100, blank=True)
    tgl_sk      = models.DateField(null=True, blank=True)
    tmt_jabatan = models.DateField(null=True, blank=True)
    is_aktif    = models.BooleanField(default=True)
    keterangan  = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt_jabatan']
        verbose_name = "Jabatan Struktural Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} – {self.jabatan}"


# ─────────────────────────────────────────────────────────────────────────────
# TUGAS TAMBAHAN
# ─────────────────────────────────────────────────────────────────────────────

class TugasTambahanTendik(models.Model):
    tendik      = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='tugas_tambahan')
    jabatan     = models.CharField(max_length=200)
    no_sk       = models.CharField(max_length=100, blank=True)
    tgl_sk      = models.DateField(null=True, blank=True)
    tmt_jabatan = models.DateField(null=True, blank=True)
    is_aktif    = models.BooleanField(default=True)
    keterangan  = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt_jabatan']
        verbose_name = "Tugas Tambahan Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} – {self.jabatan}"


# ─────────────────────────────────────────────────────────────────────────────
# PENDIDIKAN
# ─────────────────────────────────────────────────────────────────────────────

class RiwayatPendidikanTendik(models.Model):
    JENJANG_CHOICES = [
        ('SD','SD'), ('SLTP','SLTP'), ('SLTA','SLTA'),
        ('D3','D3'), ('D4','D4'), ('S1','S1'), ('S2','S2'), ('S3','S3'),
        ('PROFESI','Profesi'),
    ]
    tendik        = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='riwayat_pendidikan')
    jenjang       = models.CharField(max_length=10, choices=JENJANG_CHOICES)
    bidang_studi  = models.CharField(max_length=200, blank=True, verbose_name="Program Studi")
    prodi_pddikti = models.CharField(max_length=200, blank=True, verbose_name="Prodi PDDikti")
    fakultas_pt   = models.CharField(max_length=200, blank=True, verbose_name="Fakultas PT")
    institusi     = models.CharField(max_length=200, blank=True, verbose_name="Universitas")
    tahun_lulus   = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-jenjang']
        verbose_name = "Riwayat Pendidikan Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} – {self.jenjang} {self.institusi}"


# ─────────────────────────────────────────────────────────────────────────────
# PPPK SPESIFIK
# ─────────────────────────────────────────────────────────────────────────────

class DetailPPPK(models.Model):
    """Data primer khusus PPPK yang tidak relevan untuk PNS."""
    tendik           = models.OneToOneField(Tendik, on_delete=models.CASCADE, related_name='detail_pppk')
    tmt_pppk         = models.DateField(null=True, blank=True, verbose_name="TMT PPPK")
    tmt_berkala      = models.DateField(null=True, blank=True, verbose_name="TMT Berkala")
    thn_pengangkatan = models.IntegerField(null=True, blank=True, verbose_name="Tahun Pengangkatan")
    thn_berjalan     = models.IntegerField(null=True, blank=True, verbose_name="Tahun Berjalan Kontrak")

    class Meta:
        verbose_name = "Detail PPPK"

    def __str__(self):
        return f"Detail PPPK – {self.tendik.nama_lengkap}"

    @property
    def masa_kontrak_berjalan(self):
        """(tahun, bulan) sejak TMT PPPK hingga hari ini."""
        return _selisih_tahun_bulan(self.tmt_pppk, date.today())


# ─────────────────────────────────────────────────────────────────────────────
# CUTI
# ─────────────────────────────────────────────────────────────────────────────

class CutiTendik(models.Model):
    JENIS_CHOICES = [
        ('TAHUNAN',         'Cuti Tahunan'),
        ('SAKIT',           'Cuti Sakit'),
        ('MELAHIRKAN',      'Cuti Melahirkan'),
        ('ALASAN_PENTING',  'Cuti Alasan Penting'),
        ('BESAR',           'Cuti Besar'),
        ('LUAR_TANGGUNGAN', 'Cuti Di Luar Tanggungan Negara'),
        ('IZIN',            'Izin'),
    ]
    tendik          = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='riwayat_cuti')
    jenis_cuti      = models.CharField(max_length=30, choices=JENIS_CHOICES, default='TAHUNAN')
    alasan          = models.CharField(max_length=200, blank=True)
    tanggal_mulai   = models.DateField()
    tanggal_akhir   = models.DateField()
    lama_hari_kerja = models.IntegerField(null=True, blank=True, verbose_name="Lama (Hari Kerja)")
    no_sk           = models.CharField(max_length=100, blank=True)
    keterangan      = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal_mulai']
        verbose_name = "Cuti Tendik"
        verbose_name_plural = "Cuti Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} – {self.get_jenis_cuti_display()} ({self.tanggal_mulai})"


# ─────────────────────────────────────────────────────────────────────────────
# RIWAYAT STATUS (AKTIF / CUTI / TUGAS BELAJAR / DLL)
# ─────────────────────────────────────────────────────────────────────────────

class RiwayatStatusTendik(models.Model):
    """
    Status kepegawaian yang sifatnya sementara/berulang (bukan status berhenti permanen —
    untuk itu pakai RiwayatBerhentiTendik). jenis_cuti mengambil pilihan yang sama
    persis dengan CutiTendik.JENIS_CHOICES agar tidak ada dua sumber data jenis cuti.
    """
    STATUS_CHOICES = [
        ('AKTIF',         'Aktif'),
        ('CUTI',          'Cuti'),
        ('TUGAS_BELAJAR', 'Tugas Belajar'),
        ('IZIN_BELAJAR',  'Izin Belajar'),
        ('CLTN',          'CLTN'),
    ]

    tendik = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='riwayat_status')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    jenis_cuti = models.CharField(
        max_length=30,
        choices=CutiTendik.JENIS_CHOICES,   # [reuse] ambil dari master jenis cuti yang sudah ada
        null=True, blank=True,
        verbose_name="Jenis Cuti"
    )
    tanggal_mulai = models.DateField()
    tanggal_akhir = models.DateField(null=True, blank=True)
    no_sk         = models.CharField(max_length=100, blank=True)
    keterangan    = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal_mulai']
        verbose_name = "Riwayat Status Tendik"
        verbose_name_plural = "Riwayat Status Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} – {self.get_status_display()}"


# ─────────────────────────────────────────────────────────────────────────────
# BERHENTI / MENINGGAL
# ─────────────────────────────────────────────────────────────────────────────

class RiwayatBerhentiTendik(models.Model):
    ALASAN_CHOICES = [
        ('PENSIUN',       'Pensiun'),
        ('PENSIUN_DINI',  'Pensiun Dini'),
        ('MENINGGAL',     'Meninggal Dunia'),
        ('PINDAH',        'Pindah Instansi'),
        ('DIBERHENTIKAN', 'Diberhentikan'),
        ('LAINNYA',       'Lainnya'),
    ]
    tendik           = models.OneToOneField(Tendik, on_delete=models.CASCADE, related_name='riwayat_berhenti')
    alasan           = models.CharField(max_length=30, choices=ALASAN_CHOICES)
    tanggal          = models.DateField()
    no_sk            = models.CharField(max_length=100, blank=True)
    no_telp_keluarga = models.CharField(max_length=30, blank=True, verbose_name="No. Telp Keluarga")
    keterangan       = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Riwayat Berhenti Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} – {self.get_alasan_display()} ({self.tanggal})"


# ─────────────────────────────────────────────────────────────────────────────
# KELUARGA
# ─────────────────────────────────────────────────────────────────────────────

class KeluargaTendik(models.Model):
    STATUS_HUBUNGAN_CHOICES = [
        ('SUAMI', 'Suami'),
        ('ISTRI', 'Istri'),
        ('ANAK',  'Anak'),
    ]

    tendik = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='keluarga')
    nama = models.CharField(max_length=200)
    status_hubungan = models.CharField(max_length=20, choices=STATUS_HUBUNGAN_CHOICES)
    tanggal_lahir = models.DateField(null=True, blank=True)
    pekerjaan = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['status_hubungan', 'tanggal_lahir']
        verbose_name = "Keluarga Tendik"
        verbose_name_plural = "Keluarga Tendik"

    def __str__(self):
        return f"{self.nama} ({self.get_status_hubungan_display()})"