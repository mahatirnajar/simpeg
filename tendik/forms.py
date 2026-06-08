from django import forms
from .models import (
    Tendik, UnitKerja,
    RiwayatKepangkatanTendik, RiwayatJabatanFungsionalTendik,
    JabatanStrukturalTendik, RiwayatPendidikanTendik,
    TugasTambahanTendik, MasaKerjaTendik,
)

_INPUT   = {'class': 'form-control'}
_SELECT  = {'class': 'form-select'}
_DATE    = {'type': 'date', 'class': 'form-control'}
_NUMBER  = {'class': 'form-control'}
_AREA    = {'class': 'form-control', 'rows': 2}
_CHECK   = {'class': 'form-check-input'}


class TendikForm(forms.ModelForm):
    class Meta:
        model = Tendik
        exclude = ['created_at', 'updated_at', 'created_by']
        widgets = {
            'nama_lengkap':        forms.TextInput(_INPUT),
            'nama_terang':         forms.TextInput(_INPUT),
            'gelar_depan':         forms.TextInput(_INPUT),
            'gelar_belakang':      forms.TextInput(_INPUT),
            'nidn':                forms.TextInput(_INPUT),
            'nuptk':               forms.TextInput(_INPUT),
            'nip':                 forms.TextInput(_INPUT),
            'no_ktp':              forms.TextInput(_INPUT),
            'karpeg':              forms.TextInput(_INPUT),
            'nira':                forms.TextInput(_INPUT),
            'tempat_lahir':        forms.TextInput(_INPUT),
            'tanggal_lahir':       forms.DateInput(_DATE),
            'jenis_kelamin':       forms.Select(_SELECT),
            'agama':               forms.Select(_SELECT),
            'status':              forms.Select(_SELECT),
            'fakultas':            forms.Select(_SELECT),
            'unit_kerja':          forms.Select(_SELECT),
            'bagian':              forms.TextInput(_INPUT),
            'tmt_cpns':            forms.DateInput(_DATE),
            'tmt_pns':             forms.DateInput(_DATE),
            'bidang_keahlian':     forms.TextInput(_INPUT),
            'tingkat_ijazah_bkn':  forms.TextInput(_INPUT),
            'tingkat_ijazah_borang': forms.TextInput(_INPUT),
            'usia_pensiun':        forms.NumberInput(_NUMBER),
            'tahun_pensiun':       forms.NumberInput(_NUMBER),
        }


class RiwayatKepangkatanTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatKepangkatanTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'pangkat':     forms.TextInput(_INPUT),
            'golongan':    forms.TextInput(_INPUT),
            'tmt':         forms.DateInput(_DATE),
            'keterangan':  forms.Textarea(_AREA),
        }


class RiwayatJabatanFungsionalTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatJabatanFungsionalTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'jenjang':      forms.TextInput(_INPUT),
            'tmt':          forms.DateInput(_DATE),
            'angka_kredit': forms.NumberInput({**_NUMBER, 'step': '0.01'}),
            'keterangan':   forms.Textarea(_AREA),
        }


class JabatanStrukturalTendikForm(forms.ModelForm):
    class Meta:
        model = JabatanStrukturalTendik
        exclude = ['tendik', 'created_at']
        widgets = {
            'jabatan':     forms.TextInput(_INPUT),
            'eselon':      forms.Select(_SELECT),
            'unit_kerja':  forms.TextInput(_INPUT),
            'no_sk':       forms.TextInput(_INPUT),
            'tgl_sk':      forms.DateInput(_DATE),
            'tmt_jabatan': forms.DateInput(_DATE),
            'is_aktif':    forms.CheckboxInput(_CHECK),
            'keterangan':  forms.Textarea(_AREA),
        }


class RiwayatPendidikanTendikForm(forms.ModelForm):
    class Meta:
        model = RiwayatPendidikanTendik
        exclude = ['tendik']
        widgets = {
            'jenjang':      forms.TextInput(_INPUT),
            'bidang_studi': forms.TextInput(_INPUT),
            'institusi':    forms.TextInput(_INPUT),
            'tahun_lulus':  forms.NumberInput(_NUMBER),
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
            'is_aktif':    forms.CheckboxInput(_CHECK),
            'keterangan':  forms.Textarea(_AREA),
        }


class MasaKerjaTendikForm(forms.ModelForm):
    class Meta:
        model = MasaKerjaTendik
        exclude = ['tendik', 'tanggal_update']
        widgets = {f: forms.NumberInput(_NUMBER) for f in [
            'cpns_tahun', 'cpns_bulan', 'golongan_tahun', 'golongan_bulan',
            'jabatan_tahun', 'jabatan_bulan', 'keseluruhan_tahun', 'keseluruhan_bulan',
            'pensiun_tahun', 'pensiun_bulan',
        ]}


class UnitKerjaForm(forms.ModelForm):
    class Meta:
        model = UnitKerja
        fields = '__all__'
        widgets = {
            'kode':   forms.TextInput(_INPUT),
            'nama':   forms.TextInput(_INPUT),
            'induk':  forms.Select(_SELECT),
            'jenis':  forms.Select(_SELECT),
        }
