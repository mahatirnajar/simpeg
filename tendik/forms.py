from django import forms
from django.core.exceptions import ValidationError
from .models import (
    KeluargaTendik, RiwayatStatusTendik, Tendik, UnitKerja,
    RiwayatKepangkatanTendik, RiwayatJabatanFungsionalTendik,
    JabatanStrukturalTendik, RiwayatPendidikanTendik,
    TugasTambahanTendik, RiwayatBerhentiTendik,
    RiwayatStatusTendik, KeluargaTendik,
)

_INPUT  = {'class': 'form-control'}
_SELECT = {'class': 'form-select'}
_DATE   = {'type': 'date', 'class': 'form-control'}
_NUMBER = {'class': 'form-control'}
_AREA   = {'class': 'form-control', 'rows': 2}
_CHECK  = {'class': 'form-check-input'}


class TendikForm(forms.ModelForm):
    class Meta:
        model = Tendik
        exclude = ['created_at', 'updated_at', 'created_by']

        widgets = {
            # =========================
            # NAMA
            # =========================
            'gelar_depan': forms.TextInput({
                **_INPUT,
                'placeholder': 'Dr. / Drs. / Prof. (kosongkan jika tidak ada)'
            }),

            'nama_terang': forms.TextInput({
                **_INPUT,
                'placeholder': 'Nama tanpa gelar'
            }),

            'gelar_belakang': forms.TextInput({
                **_INPUT,
                'placeholder': 'S.E., M.M. (kosongkan jika tidak ada)'
            }),

            # =========================
            # IDENTITAS
            # =========================
            'nuptk': forms.TextInput({
                **_INPUT,
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
                'maxlength': '16'
            }),

            'nip': forms.TextInput({
                **_INPUT,
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
                'maxlength': '18'
            }),

            'no_ktp': forms.TextInput({
                **_INPUT,
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
                'maxlength': '16'
            }),

            # =========================
            # DATA PRIBADI
            # =========================
            'tempat_lahir': forms.TextInput(_INPUT),

            'tanggal_lahir': forms.DateInput(_DATE),

            'jenis_kelamin': forms.Select(_SELECT),

            'agama': forms.Select(_SELECT),

            # =========================
            # KONTAK
            # =========================
            'no_hp': forms.TextInput({
                **_INPUT,
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
                'maxlength': '15',
                'placeholder': '08xxxxxxxxxx'
            }),

            'email': forms.EmailInput(_INPUT),

            'alamat': forms.Textarea(_AREA),

            # =========================
            # UNIT KERJA
            # =========================
            'status': forms.Select(_SELECT),

            'unit_kerja': forms.Select(_SELECT),

            'bagian': forms.TextInput(_INPUT),

            # =========================
            # KEPEGAWAIAN
            # =========================
            'tmt_cpns': forms.DateInput(_DATE),

            'tmt_pns': forms.DateInput(_DATE),

            'tmt_kgb': forms.DateInput(_DATE),

            # =========================
            # PENDIDIKAN
            # =========================
            'bidang_keahlian': forms.TextInput(_INPUT),

            'tingkat_ijazah_bkn': forms.Select(_SELECT),

            'tingkat_ijazah_borang': forms.TextInput(_INPUT),

            'tingkat_ijazah_profesi': forms.CheckboxInput(_CHECK),

            # =========================
            # PENSIUN
            # =========================
            'usia_pensiun': forms.NumberInput({
                **_NUMBER,
                'min': 56,
                'max': 65
            }),

            'tmt_pensiun': forms.DateInput(attrs=_DATE, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['nama_terang'].help_text = (
            'Nama tanpa gelar. Nama lengkap akan otomatis menjadi '
            '<em>Gelar Depan + Nama Terang + Gelar Belakang</em>.'
        )

        self.fields['usia_pensiun'].help_text = (
            'PNS biasanya 60 tahun dan PPPK 58 tahun. '
            'Tanggal dan tahun pensiun dihitung otomatis.'
        )

        self.fields['tmt_pensiun'].help_text = (
            'Otomatis terisi saat tendik baru dibuat. Bisa diubah manual jika perlu.'
        )

        for name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'

        if self.is_bound:
            for name, field in self.fields.items():
                if name in self.errors:
                    css = field.widget.attrs.get('class', '')
                    field.widget.attrs['class'] = f'{css} is-invalid'

    # ==================================================
    # HELPER VALIDATOR
    # ==================================================
    def _validate_numeric(self, value, label, length=None):
        if not value:
            return value

        if not value.isdigit():
            raise ValidationError(
                f'{label} hanya boleh berisi angka.'
            )

        if length and len(value) != length:
            raise ValidationError(
                f'{label} harus {length} digit.'
            )

        return value

    # ==================================================
    # VALIDASI NIP
    # ==================================================
    def clean_nip(self):
        return self._validate_numeric(
            self.cleaned_data.get('nip'),
            'NIP',
            18
        )

    # ==================================================
    # VALIDASI NUPTK
    # ==================================================
    def clean_nuptk(self):
        return self._validate_numeric(
            self.cleaned_data.get('nuptk'),
            'NUPTK',
            16
        )

    # ==================================================
    # VALIDASI NIK
    # ==================================================
    def clean_no_ktp(self):
        return self._validate_numeric(
            self.cleaned_data.get('no_ktp'),
            'NIK',
            16
        )

    # ==================================================
    # VALIDASI HP
    # ==================================================
    def clean_no_hp(self):
        hp = self.cleaned_data.get('no_hp')

        if not hp:
            return hp

        if not hp.isdigit():
            raise ValidationError(
                'Nomor HP hanya boleh berisi angka.'
            )

        if len(hp) < 10 or len(hp) > 15:
            raise ValidationError(
                'Nomor HP harus terdiri dari 10 sampai 15 digit.'
            )

        if not hp.startswith('0'):
            raise ValidationError(
                'Nomor HP harus diawali angka 0.'
            )

        return hp


class RiwayatKepangkatanTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatKepangkatanTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'pangkat':    forms.TextInput({**_INPUT, 'placeholder': 'Penata Muda / Pembina Utama Muda / ...'}),
            'golongan':   forms.TextInput({**_INPUT, 'placeholder': 'III/a atau IX (PPPK)'}),
            'tmt':        forms.DateInput(_DATE),
            'keterangan': forms.Textarea(_AREA),
            'dokumen_pendukung': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
        }

    def __init__(self, *args, **kwargs):
        super(RiwayatKepangkatanTendikForm, self).__init__(*args, **kwargs)
        # Baris ini yang membuat field menjadi wajib diisi pada form
        self.fields['dokumen_pendukung'].required = True 
        
        # Opsional: Menambahkan pesan error kustom jika tidak diisi
        self.fields['dokumen_pendukung'].error_messages = {
            'required': 'URL Dokumen pendukung wajib dilampirkan!'
        }
        

class RiwayatJabatanFungsionalTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatJabatanFungsionalTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'jenis':        forms.Select(_SELECT),
            'nama_jabatan': forms.TextInput({**_INPUT, 'placeholder': 'Pustakawan / Pranata Komputer / Apoteker / ...'}),
            'jenjang':      forms.Select(_SELECT),
            'tmt':          forms.DateInput(_DATE),
            'angka_kredit': forms.NumberInput({**_NUMBER, 'step': '0.01'}),
            'keterangan':   forms.Textarea(_AREA),
            'dokumen_pendukung': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
        }
    def __init__(self, *args, **kwargs):
        super(RiwayatJabatanFungsionalTendikForm, self).__init__(*args, **kwargs)
        # Baris ini yang membuat field menjadi wajib diisi pada form
        self.fields['dokumen_pendukung'].required = True 
        
        # Opsional: Menambahkan pesan error kustom jika tidak diisi
        self.fields['dokumen_pendukung'].error_messages = {
            'required': 'URL Dokumen pendukung wajib dilampirkan!'
        }


class JabatanStrukturalTendikForm(forms.ModelForm):
    class Meta:
        model = JabatanStrukturalTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'jabatan':     forms.TextInput({**_INPUT, 'placeholder': 'Kepala Biro / Kepala Bagian / ...'}),
            'jenjang':     forms.TextInput(_INPUT),
            'eselon':      forms.Select(_SELECT),
            'unit_kerja':  forms.TextInput(_INPUT),
            'no_sk':       forms.TextInput(_INPUT),
            'tgl_sk':      forms.DateInput(_DATE),
            'tmt_jabatan': forms.DateInput(_DATE),
            'is_aktif':    forms.CheckboxInput(_CHECK),
            'keterangan':  forms.Textarea(_AREA),
            'dokumen_pendukung': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
        }
    def __init__(self, *args, **kwargs):
        super(JabatanStrukturalTendikForm, self).__init__(*args, **kwargs)
        # Baris ini yang membuat field menjadi wajib diisi pada form
        self.fields['dokumen_pendukung'].required = True 
        
        # Opsional: Menambahkan pesan error kustom jika tidak diisi
        self.fields['dokumen_pendukung'].error_messages = {
            'required': 'URL Dokumen pendukung wajib dilampirkan!'
        }


class RiwayatPendidikanTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatPendidikanTendik
        exclude = ['tendik']
        widgets = {
            'jenjang':       forms.Select(_SELECT),
            'bidang_studi':  forms.TextInput(_INPUT),
            'prodi_pddikti': forms.TextInput(_INPUT),
            'fakultas_pt':   forms.TextInput(_INPUT),
            'institusi':     forms.TextInput(_INPUT),
            'tahun_lulus':   forms.NumberInput({**_NUMBER, 'min': 1970, 'max': 2030}),
            'dokumen_pendukung': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
        }
    def __init__(self, *args, **kwargs):
        super(JabatanStrukturalTendikForm, self).__init__(*args, **kwargs)
        # Baris ini yang membuat field menjadi wajib diisi pada form
        self.fields['dokumen_pendukung'].required = True 
        
        # Opsional: Menambahkan pesan error kustom jika tidak diisi
        self.fields['dokumen_pendukung'].error_messages = {
            'required': 'URL Dokumen pendukung wajib dilampirkan!'
        }


class TugasTambahanTendikForm(forms.ModelForm):
    class Meta:
        model = TugasTambahanTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'jabatan':     forms.TextInput(_INPUT),
            'no_sk':       forms.TextInput(_INPUT),
            'tgl_sk':      forms.DateInput(_DATE),
            'tmt_jabatan': forms.DateInput(_DATE),
            'dokumen_pendukung': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            'is_aktif':    forms.CheckboxInput(_CHECK),
            'keterangan':  forms.Textarea(_AREA),
        }
    def __init__(self, *args, **kwargs):
        super(TugasTambahanTendikForm, self).__init__(*args, **kwargs)
        # Baris ini yang membuat field menjadi wajib diisi pada form
        self.fields['dokumen_pendukung'].required = True 
        
        # Opsional: Menambahkan pesan error kustom jika tidak diisi
        self.fields['dokumen_pendukung'].error_messages = {
            'required': 'URL Dokumen pendukung wajib dilampirkan!'
        }

class RiwayatBerhentiTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatBerhentiTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'alasan':           forms.Select(_SELECT),
            'tanggal':          forms.DateInput(attrs=_DATE, format='%Y-%m-%d'),
            'no_sk':            forms.TextInput(_INPUT),
            'no_telp_keluarga': forms.TextInput(_INPUT),
            'keterangan':       forms.Textarea(_AREA),
        }


class RiwayatStatusTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatStatusTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'status': forms.Select(_SELECT),
            'jenis_cuti': forms.Select({**_SELECT, 'id': 'id_jenis_cuti'}),
            'tanggal_mulai': forms.DateInput(attrs=_DATE, format='%Y-%m-%d'),
            'tanggal_akhir': forms.DateInput(attrs=_DATE, format='%Y-%m-%d'),
            'no_sk': forms.TextInput(_INPUT),
            'keterangan': forms.Textarea(_AREA),
        }


class KeluargaTendikForm(forms.ModelForm):
    class Meta:
        model = KeluargaTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'nama': forms.TextInput(_INPUT),
            'status_hubungan': forms.Select(_SELECT),
            'tanggal_lahir': forms.DateInput(attrs=_DATE, format='%Y-%m-%d'),
            'pekerjaan': forms.TextInput(_INPUT),
        }


class UnitKerjaForm(forms.ModelForm):
    class Meta:
        model  = UnitKerja
        fields = '__all__'
        widgets = {
            'kode':  forms.TextInput(_INPUT),
            'nama':  forms.TextInput(_INPUT),
        }

class RiwayatStatusTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatStatusTendik
        exclude = ['tendik']

        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),

            'jenis_cuti': forms.Select(attrs={
                'class': 'form-select', 
                'id': 'id_jenis_cuti'
            }),

            'tanggal_mulai': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'tanggal_akhir': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'no_sk': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'dokumen_pendukung': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://drive.google.com/...'
            }),

            'keterangan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            
        }
    def __init__(self, *args, **kwargs):
        super(RiwayatStatusTendikForm, self).__init__(*args, **kwargs)
        # Baris ini yang membuat field menjadi wajib diisi pada form
        self.fields['dokumen_pendukung'].required = True 
        
        # Opsional: Menambahkan pesan error kustom jika tidak diisi
        self.fields['dokumen_pendukung'].error_messages = {
            'required': 'URL Dokumen pendukung wajib dilampirkan!'
        }

class KeluargaTendikForm(forms.ModelForm):
    class Meta:
        model = KeluargaTendik
        exclude = ['tendik', 'created_at']

        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'status_hubungan': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_lahir': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'pekerjaan': forms.TextInput(attrs={'class': 'form-control'}),
            'dokumen_pendukung': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
        }

    def __init__(self, *args, **kwargs):
        super(KeluargaTendikForm, self).__init__(*args, **kwargs)
        # Baris ini yang membuat field menjadi wajib diisi pada form
        self.fields['dokumen_pendukung'].required = True 
        
        # Opsional: Menambahkan pesan error kustom jika tidak diisi
        self.fields['dokumen_pendukung'].error_messages = {
            'required': 'URL Dokumen pendukung wajib dilampirkan!'
        }