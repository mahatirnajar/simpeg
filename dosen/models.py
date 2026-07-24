from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Fakultas(models.Model):
    kode = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Fakultas"
        ordering = ['nama']

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class ProgramStudi(models.Model):
    fakultas = models.ForeignKey(Fakultas, on_delete=models.CASCADE, related_name='program_studi')
    nama = models.CharField(max_length=200)
    jenjang = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ['nama']

    def __str__(self):
        return self.nama


class Dosen(models.Model):
    JENIS_KELAMIN_CHOICES = [('L', 'Laki-laki'), ('P', 'Perempuan')]
    AGAMA_CHOICES = [
        ('Islam', 'Islam'), ('Kristen', 'Kristen'), ('Katolik', 'Katolik'),
        ('Hindu', 'Hindu'), ('Budha', 'Budha'), ('Konghucu', 'Konghucu'),
    ]
    STATUS_CHOICES = [('PNS', 'PNS'), ('CPNS', 'CPNS'), ('PPPK', 'PPPK'), ('Non-PNS', 'Non-PNS')]

    nidn = models.CharField(max_length=20, null=True, blank=True, verbose_name="NIDN")
    nuptk = models.CharField(max_length=30, null=True, blank=True, verbose_name="NUPTK")
    nip = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name="NIP")
    no_ktp = models.CharField(max_length=20, null=True, blank=True, verbose_name="No. KTP")
    karpeg = models.CharField(max_length=20, null=True, blank=True, verbose_name="KARPEG")
    nira = models.CharField(max_length=50, null=True, blank=True, verbose_name="NIRA")
    no_reg_serdos = models.CharField(max_length=30, null=True, blank=True, verbose_name="No. Reg. Serdos")

    nama_lengkap = models.CharField(max_length=200, verbose_name="Nama Lengkap (dengan gelar)")
    nama_terang = models.CharField(max_length=200, verbose_name="Nama Terang (tanpa gelar)")
    gelar_depan = models.CharField(max_length=100, blank=True, verbose_name="Gelar Depan")
    gelar_belakang = models.CharField(max_length=100, blank=True, verbose_name="Gelar Belakang")

    jenis_kelamin = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES)
    agama = models.CharField(max_length=20, choices=AGAMA_CHOICES, blank=True)
    tempat_lahir = models.CharField(max_length=100, blank=True)
    tanggal_lahir = models.DateField(null=True, blank=True)

    fakultas = models.ForeignKey(Fakultas, on_delete=models.SET_NULL, null=True, related_name='dosen')
    jurusan_bagian = models.CharField(max_length=200, blank=True, verbose_name="Jurusan/Bagian")
    program_studi_nama = models.CharField(max_length=200, blank=True, verbose_name="Program Studi")
    jenjang_prodi = models.CharField(max_length=10, blank=True, verbose_name="Jenjang Prodi")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PNS')
    tmt_cpns = models.DateField(null=True, blank=True, verbose_name="TMT CPNS")
    tmt_pns = models.DateField(null=True, blank=True, verbose_name="TMT PNS")

    ranting_ilmu = models.CharField(max_length=300, blank=True, verbose_name="Ranting Ilmu/Kepakaran")
    tingkat_ijazah_bkn = models.CharField(max_length=10, blank=True, verbose_name="Tingkat Ijazah BKN")
    tingkat_ijazah_borang = models.CharField(max_length=10, blank=True, verbose_name="Tingkat Ijazah Borang")

    usia_pensiun = models.IntegerField(null=True, blank=True, verbose_name="Usia Pensiun")
    tahun_pensiun = models.IntegerField(null=True, blank=True, verbose_name="Tahun Pensiun")
    tmt_pensiun = models.DateField(null=True, blank=True, verbose_name="TMT Pensiun (BUP)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dosen_created')

    class Meta:
        ordering = ['nama_lengkap']
        verbose_name_plural = "Dosen"

    def __str__(self):
        return self.nama_lengkap

    @property
    def kepangkatan_terakhir(self):
        return self.riwayat_kepangkatan.order_by('-tmt').first()

    @property
    def jabatan_fungsional_terakhir(self):
        return self.riwayat_jabatan_fungsional.order_by('-tmt').first()

    @property
    def tugas_tambahan_aktif(self):
        return self.tugas_tambahan.filter(is_aktif=True).first()

    @property
    def usia_saat_ini(self):
        if self.tanggal_lahir:
            from datetime import date
            today = date.today()
            return today.year - self.tanggal_lahir.year - (
                (today.month, today.day) < (self.tanggal_lahir.month, self.tanggal_lahir.day)
            )
        return None

    @property
    def status_terakhir(self):
        return self.riwayat_status.order_by('-tanggal_mulai').first()

    def _hitung_usia_bup(self):
        """Usia BUP: pakai field usia_pensiun jika diisi manual,
        jika tidak: Guru Besar = 70 tahun, selain itu = 65 tahun."""
        if self.usia_pensiun:
            return self.usia_pensiun
        jf = self.jabatan_fungsional_terakhir
        if jf and 'guru besar' in jf.jenjang.lower():
            return 70
        return 65

    def hitung_tmt_pensiun(self):
        """Hitung TMT Pensiun (tanggal lahir + usia BUP). Tidak menyimpan ke DB."""
        if not self.tanggal_lahir:
            return None
        tahun = self._hitung_usia_bup()
        try:
            return self.tanggal_lahir.replace(year=self.tanggal_lahir.year + tahun)
        except ValueError:
            return self.tanggal_lahir.replace(month=2, day=28, year=self.tanggal_lahir.year + tahun)

    def save(self, *args, **kwargs):
        # Auto-hitung tmt_pensiun HANYA jika masih kosong (dosen baru / belum pernah diisi).
        # Jika admin sudah mengisi/mengubahnya secara manual, nilai itu tidak akan ditimpa.
        is_new = self.pk is None

        if not is_new and not self.tmt_pensiun:
            self.tmt_pensiun = self.hitung_tmt_pensiun()

        super().save(*args, **kwargs)

        if is_new and not self.tmt_pensiun and self.tanggal_lahir:
            tmt = self.hitung_tmt_pensiun()
            if tmt:
                Dosen.objects.filter(pk=self.pk).update(tmt_pensiun=tmt)
                self.tmt_pensiun = tmt

    @property
    def sudah_bup(self):
        from datetime import date
        return bool(self.tmt_pensiun and self.tmt_pensiun <= date.today())

    @property
    def lama_lewat_bup(self):
        """(tahun, bulan) sejak mencapai BUP. None jika belum BUP / tmt_pensiun kosong."""
        from datetime import date
        if not self.tmt_pensiun:
            return None
        today = date.today()
        if self.tmt_pensiun > today:
            return None
        selisih_bulan = (today.year - self.tmt_pensiun.year) * 12 + (today.month - self.tmt_pensiun.month)
        if today.day < self.tmt_pensiun.day:
            selisih_bulan -= 1
        return divmod(max(selisih_bulan, 0), 12)


class RiwayatKepangkatan(models.Model):
    dosen = models.ForeignKey(Dosen, on_delete=models.CASCADE, related_name='riwayat_kepangkatan')
    pangkat = models.CharField(max_length=100)
    golongan = models.CharField(max_length=10)
    tmt = models.DateField()
    keterangan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt']

    def __str__(self):
        return f"{self.dosen.nama_lengkap} - {self.pangkat} ({self.golongan})"


class RiwayatJabatanFungsional(models.Model):
    dosen = models.ForeignKey(Dosen, on_delete=models.CASCADE, related_name='riwayat_jabatan_fungsional')
    jenjang = models.CharField(max_length=100)
    tmt = models.DateField()
    angka_kredit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    keterangan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt']

    def __str__(self):
        return f"{self.dosen.nama_lengkap} - {self.jenjang}"


class RiwayatPendidikan(models.Model):
    dosen = models.ForeignKey(Dosen, on_delete=models.CASCADE, related_name='riwayat_pendidikan')
    jenjang = models.CharField(max_length=10)
    bidang_studi = models.CharField(max_length=200, blank=True)
    institusi = models.CharField(max_length=200, blank=True)
    tahun_lulus = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-jenjang']

    def __str__(self):
        return f"{self.dosen.nama_lengkap} - {self.jenjang}"


class TugasTambahan(models.Model):
    dosen = models.ForeignKey(Dosen, on_delete=models.CASCADE, related_name='tugas_tambahan')
    jabatan = models.CharField(max_length=200)
    no_sk = models.CharField(max_length=100, blank=True)
    tgl_sk = models.DateField(null=True, blank=True)
    tmt_jabatan = models.DateField(null=True, blank=True)
    is_aktif = models.BooleanField(default=True)
    keterangan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tmt_jabatan']

    def __str__(self):
        return f"{self.dosen.nama_lengkap} - {self.jabatan}"


class MasaKerja(models.Model):
    dosen = models.OneToOneField(Dosen, on_delete=models.CASCADE, related_name='masa_kerja')
    cpns_tahun = models.IntegerField(null=True, blank=True)
    cpns_bulan = models.IntegerField(null=True, blank=True)
    golongan_tahun = models.IntegerField(null=True, blank=True)
    golongan_bulan = models.IntegerField(null=True, blank=True)
    jabatan_tahun = models.IntegerField(null=True, blank=True)
    jabatan_bulan = models.IntegerField(null=True, blank=True)
    keseluruhan_tahun = models.IntegerField(null=True, blank=True)
    keseluruhan_bulan = models.IntegerField(null=True, blank=True)
    pensiun_tahun = models.IntegerField(null=True, blank=True)
    pensiun_bulan = models.IntegerField(null=True, blank=True)
    tanggal_update = models.DateField(auto_now=True)

    def __str__(self):
        return f"Masa Kerja {self.dosen.nama_lengkap}"


class RiwayatStatusDosen(models.Model):
    STATUS_CHOICES = [
        ('AKTIF', 'Aktif'),
        ('CUTI', 'Cuti'),
        ('TUGAS_BELAJAR', 'Tugas Belajar'),
        ('IZIN_BELAJAR', 'Izin Belajar'),
        ('CLTN', 'CLTN'),
        ('PENSIUN', 'Pensiun'),
        ('MENINGGAL', 'Meninggal'),
        ('PINDAH', 'Pindah Instansi'),
        ('BERHENTI', 'Berhenti'),
    ]

    JENIS_CUTI_CHOICES = [
        ('TAHUNAN', 'Cuti Tahunan'),
        ('BESAR', 'Cuti Besar'),
        ('SAKIT', 'Cuti Sakit'),
        ('MELAHIRKAN', 'Cuti Melahirkan'),
        ('ALASAN_PENTING', 'Cuti Karena Alasan Penting'),
        ('DILUAR_TANGGUNGAN_NEGARA', 'Cuti di Luar Tanggungan Negara'),
    ]

    dosen = models.ForeignKey(
        Dosen,
        on_delete=models.CASCADE,
        related_name='riwayat_status'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES
    )
    jenis_cuti = models.CharField(max_length=50, 
                                  choices=JENIS_CUTI_CHOICES, 
                                  null=True, 
                                  blank=True)

    tanggal_mulai = models.DateField()
    tanggal_akhir = models.DateField(
        null=True,
        blank=True
    )

    no_sk = models.CharField(
        max_length=100,
        blank=True
    )

    keterangan = models.TextField(
        blank=True
    )


class KeluargaDosen(models.Model):
    STATUS_HUBUNGAN_CHOICES = [
        ('SUAMI', 'Suami'),
        ('ISTRI', 'Istri'),
        ('ANAK', 'Anak'),
    ]

    dosen = models.ForeignKey(
        Dosen, 
        on_delete=models.CASCADE, 
        related_name='keluarga'
    )
    nama = models.CharField(max_length=200)
    status_hubungan = models.CharField(max_length=20, choices=STATUS_HUBUNGAN_CHOICES)
    tanggal_lahir = models.DateField(null=True, blank=True)
    pekerjaan = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['status_hubungan', 'tanggal_lahir']

    def __str__(self):
        return f"{self.nama} ({self.get_status_hubungan_display()})"


# ── Signal: recalculate tmt_pensiun saat riwayat jabatan fungsional berubah ──
# (mis. dosen naik jabatan ke Guru Besar -> BUP berubah dari 65 ke 70 tahun,
# tmt_pensiun dosen terkait harus ikut diperbarui otomatis)

@receiver(post_save, sender=RiwayatJabatanFungsional)
def _update_tmt_pensiun_on_jabatan_save(sender, instance, **kwargs):
    dosen = instance.dosen
    # Hanya isi otomatis jika dosen belum punya tmt_pensiun manual
    if not dosen.tmt_pensiun:
        tmt_baru = dosen.hitung_tmt_pensiun()
        if tmt_baru:
            Dosen.objects.filter(pk=dosen.pk).update(tmt_pensiun=tmt_baru)


@receiver(post_delete, sender=RiwayatJabatanFungsional)
def _update_tmt_pensiun_on_jabatan_delete(sender, instance, **kwargs):
    dosen = instance.dosen
    if not dosen.tmt_pensiun:
        tmt_baru = dosen.hitung_tmt_pensiun()
        if tmt_baru:
            Dosen.objects.filter(pk=dosen.pk).update(tmt_pensiun=tmt_baru)