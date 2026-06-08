from django.db import models
from django.contrib.auth.models import User
from dosen.models import Fakultas  # Share Fakultas dari app dosen


class UnitKerja(models.Model):
    """
    Unit kerja tendik bisa berupa: Biro, Bagian, Sub-bagian, UPT, dll.
    Berbeda dengan dosen yang unit kerjanya Fakultas/Jurusan.
    """
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=200)
    induk = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sub_unit', verbose_name="Unit Induk"
    )
    jenis = models.CharField(
        max_length=30,
        choices=[
            ('REKTORAT', 'Rektorat'),
            ('BIRO', 'Biro'),
            ('BAGIAN', 'Bagian'),
            ('SUB_BAGIAN', 'Sub-Bagian'),
            ('UPT', 'UPT'),
            ('FAKULTAS', 'Fakultas'),
            ('LEMBAGA', 'Lembaga'),
            ('LAINNYA', 'Lainnya'),
        ],
        default='BAGIAN'
    )

    class Meta:
        verbose_name = "Unit Kerja"
        verbose_name_plural = "Unit Kerja"
        ordering = ['nama']

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class Tendik(models.Model):
    JENIS_KELAMIN_CHOICES = [('L', 'Laki-laki'), ('P', 'Perempuan')]
    AGAMA_CHOICES = [
        ('Islam', 'Islam'), ('Kristen', 'Kristen'), ('Katolik', 'Katolik'),
        ('Hindu', 'Hindu'), ('Budha', 'Budha'), ('Konghucu', 'Konghucu'),
    ]
    STATUS_CHOICES = [('PNS', 'PNS'), ('CPNS', 'CPNS'), ('PPPK', 'PPPK'), ('Non-PNS', 'Non-PNS')]

    # ── Identitas ────────────────────────────────────────────────────────────
    nidn   = models.CharField(max_length=20,  null=True, blank=True, verbose_name="NIDN/NI")
    nuptk  = models.CharField(max_length=30,  null=True, blank=True, verbose_name="NUPTK")
    nip    = models.CharField(max_length=30,  unique=True, null=True, blank=True, verbose_name="NIP")
    no_ktp = models.CharField(max_length=20,  null=True, blank=True, verbose_name="No. KTP")
    karpeg = models.CharField(max_length=20,  null=True, blank=True, verbose_name="KARPEG")
    nira   = models.CharField(max_length=50,  null=True, blank=True, verbose_name="NIRA")

    # ── Nama ────────────────────────────────────────────────────────────────
    nama_lengkap  = models.CharField(max_length=200, verbose_name="Nama Lengkap (dengan gelar)")
    nama_terang   = models.CharField(max_length=200, verbose_name="Nama Terang (tanpa gelar)")
    gelar_depan   = models.CharField(max_length=100, blank=True, verbose_name="Gelar Depan")
    gelar_belakang= models.CharField(max_length=100, blank=True, verbose_name="Gelar Belakang")

    # ── Data Pribadi ─────────────────────────────────────────────────────────
    jenis_kelamin = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES)
    agama         = models.CharField(max_length=20, choices=AGAMA_CHOICES, blank=True)
    tempat_lahir  = models.CharField(max_length=100, blank=True)
    tanggal_lahir = models.DateField(null=True, blank=True)

    # ── Unit Kerja ───────────────────────────────────────────────────────────
    # Tendik bisa ditempatkan di Fakultas (misal: staf TU Fakultas)
    # atau di unit non-fakultas (Biro, Bagian, UPT, dll)
    fakultas    = models.ForeignKey(
        Fakultas, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tendik', verbose_name="Fakultas (jika di Fakultas)"
    )
    unit_kerja  = models.ForeignKey(
        UnitKerja, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tendik', verbose_name="Unit Kerja"
    )
    bagian      = models.CharField(max_length=200, blank=True, verbose_name="Bagian/Sub-Bagian")

    # ── Status Kepegawaian ──────────────────────────────────────────────────
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PNS')
    tmt_cpns = models.DateField(null=True, blank=True, verbose_name="TMT CPNS")
    tmt_pns  = models.DateField(null=True, blank=True, verbose_name="TMT PNS")

    # ── Akademik / Kompetensi ────────────────────────────────────────────────
    bidang_keahlian       = models.CharField(max_length=300, blank=True, verbose_name="Bidang Keahlian")
    tingkat_ijazah_bkn    = models.CharField(max_length=10,  blank=True, verbose_name="Tingkat Ijazah BKN")
    tingkat_ijazah_borang = models.CharField(max_length=10,  blank=True, verbose_name="Tingkat Ijazah Borang")

    # ── Pensiun ──────────────────────────────────────────────────────────────
    usia_pensiun  = models.IntegerField(null=True, blank=True, verbose_name="Usia Pensiun")
    tahun_pensiun = models.IntegerField(null=True, blank=True, verbose_name="Tahun Pensiun")

    # ── Metadata ─────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='tendik_created'
    )

    class Meta:
        ordering = ['nama_lengkap']
        verbose_name = "Tenaga Kependidikan"
        verbose_name_plural = "Tenaga Kependidikan"

    def __str__(self):
        return self.nama_lengkap

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
    def nama_unit(self):
        """Kembalikan nama unit kerja tergabung (fakultas atau unit kerja)."""
        if self.fakultas:
            return self.fakultas.kode
        if self.unit_kerja:
            return self.unit_kerja.kode
        return '-'

    @property
    def usia_saat_ini(self):
        if self.tanggal_lahir:
            from datetime import date
            today = date.today()
            return today.year - self.tanggal_lahir.year - (
                (today.month, today.day) < (self.tanggal_lahir.month, self.tanggal_lahir.day)
            )
        return None


class RiwayatKepangkatanTendik(models.Model):
    tendik   = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='riwayat_kepangkatan')
    pangkat  = models.CharField(max_length=100)
    golongan = models.CharField(max_length=10)
    tmt      = models.DateField()
    keterangan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt']
        verbose_name = "Riwayat Kepangkatan Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} - {self.pangkat} ({self.golongan})"


class RiwayatJabatanFungsionalTendik(models.Model):
    """
    Tendik juga bisa memiliki jabatan fungsional tertentu,
    misal: Pustakawan, Pranata Komputer, Arsiparis, Analis, dll.
    """
    tendik       = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='riwayat_jabatan_fungsional')
    jenjang      = models.CharField(max_length=100)
    tmt          = models.DateField()
    angka_kredit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    keterangan   = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt']
        verbose_name = "Riwayat Jabatan Fungsional Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} - {self.jenjang}"


class JabatanStrukturalTendik(models.Model):
    """
    Jabatan struktural khusus untuk tendik: Kepala Biro, Kepala Bagian,
    Kepala Sub-Bagian, Kepala UPT, dll.
    """
    tendik      = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='jabatan_struktural')
    jabatan     = models.CharField(max_length=200, verbose_name="Jabatan Struktural")
    eselon      = models.CharField(
        max_length=10, blank=True,
        choices=[('II/a','II/a'),('II/b','II/b'),('III/a','III/a'),('III/b','III/b'),
                 ('IV/a','IV/a'),('IV/b','IV/b'),('Pelaksana','Pelaksana')],
        verbose_name="Eselon"
    )
    unit_kerja  = models.CharField(max_length=200, blank=True, verbose_name="Unit Kerja Jabatan")
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
        return f"{self.tendik.nama_lengkap} - {self.jabatan}"


class RiwayatPendidikanTendik(models.Model):
    tendik       = models.ForeignKey(Tendik, on_delete=models.CASCADE, related_name='riwayat_pendidikan')
    jenjang      = models.CharField(max_length=10)
    bidang_studi = models.CharField(max_length=200, blank=True)
    institusi    = models.CharField(max_length=200, blank=True)
    tahun_lulus  = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-jenjang']
        verbose_name = "Riwayat Pendidikan Tendik"

    def __str__(self):
        return f"{self.tendik.nama_lengkap} - {self.jenjang}"


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
        return f"{self.tendik.nama_lengkap} - {self.jabatan}"


class MasaKerjaTendik(models.Model):
    tendik            = models.OneToOneField(Tendik, on_delete=models.CASCADE, related_name='masa_kerja')
    cpns_tahun        = models.IntegerField(null=True, blank=True)
    cpns_bulan        = models.IntegerField(null=True, blank=True)
    golongan_tahun    = models.IntegerField(null=True, blank=True)
    golongan_bulan    = models.IntegerField(null=True, blank=True)
    jabatan_tahun     = models.IntegerField(null=True, blank=True)
    jabatan_bulan     = models.IntegerField(null=True, blank=True)
    keseluruhan_tahun = models.IntegerField(null=True, blank=True)
    keseluruhan_bulan = models.IntegerField(null=True, blank=True)
    pensiun_tahun     = models.IntegerField(null=True, blank=True)
    pensiun_bulan     = models.IntegerField(null=True, blank=True)
    tanggal_update    = models.DateField(auto_now=True)

    class Meta:
        verbose_name = "Masa Kerja Tendik"

    def __str__(self):
        return f"Masa Kerja {self.tendik.nama_lengkap}"
