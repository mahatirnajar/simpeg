from django import forms
from .models import *


class DosenForm(forms.ModelForm):
    class Meta:
        model = Dosen
        exclude = ['created_at', 'updated_at', 'created_by']
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tmt_cpns': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tmt_pns': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nama_lengkap': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_terang': forms.TextInput(attrs={'class': 'form-control'}),
            'gelar_depan': forms.TextInput(attrs={'class': 'form-control'}),
            'gelar_belakang': forms.TextInput(attrs={'class': 'form-control'}),
            'nidn': forms.TextInput(attrs={'class': 'form-control'}),
            'nuptk': forms.TextInput(attrs={'class': 'form-control'}),
            'nip': forms.TextInput(attrs={'class': 'form-control'}),
            'no_ktp': forms.TextInput(attrs={'class': 'form-control'}),
            'karpeg': forms.TextInput(attrs={'class': 'form-control'}),
            'nira': forms.TextInput(attrs={'class': 'form-control'}),
            'no_reg_serdos': forms.TextInput(attrs={'class': 'form-control'}),
            'tempat_lahir': forms.TextInput(attrs={'class': 'form-control'}),
            'jenis_kelamin': forms.Select(attrs={'class': 'form-select'}),
            'agama': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'fakultas': forms.Select(attrs={'class': 'form-select'}),
            'jurusan_bagian': forms.TextInput(attrs={'class': 'form-control'}),
            'program_studi_nama': forms.TextInput(attrs={'class': 'form-control'}),
            'jenjang_prodi': forms.TextInput(attrs={'class': 'form-control'}),
            'ranting_ilmu': forms.TextInput(attrs={'class': 'form-control'}),
            'tingkat_ijazah_bkn': forms.TextInput(attrs={'class': 'form-control'}),
            'tingkat_ijazah_borang': forms.TextInput(attrs={'class': 'form-control'}),
            'usia_pensiun': forms.NumberInput(attrs={'class': 'form-control'}),
            'tahun_pensiun': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class RiwayatKepangkatanForm(forms.ModelForm):
    class Meta:
        model = RiwayatKepangkatan
        exclude = ['dosen', 'created_at']
        widgets = {
            'pangkat': forms.TextInput(attrs={'class': 'form-control'}),
            'golongan': forms.TextInput(attrs={'class': 'form-control'}),
            'tmt': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RiwayatJabatanFungsionalForm(forms.ModelForm):
    class Meta:
        model = RiwayatJabatanFungsional
        exclude = ['dosen', 'created_at']
        widgets = {
            'jenjang': forms.TextInput(attrs={'class': 'form-control'}),
            'tmt': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'angka_kredit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RiwayatPendidikanForm(forms.ModelForm):
    class Meta:
        model = RiwayatPendidikan
        exclude = ['dosen']
        widgets = {
            'jenjang': forms.TextInput(attrs={'class': 'form-control'}),
            'bidang_studi': forms.TextInput(attrs={'class': 'form-control'}),
            'institusi': forms.TextInput(attrs={'class': 'form-control'}),
            'tahun_lulus': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TugasTambahanForm(forms.ModelForm):
    class Meta:
        model = TugasTambahan
        exclude = ['dosen', 'created_at']
        widgets = {
            'jabatan': forms.TextInput(attrs={'class': 'form-control'}),
            'no_sk': forms.TextInput(attrs={'class': 'form-control'}),
            'tgl_sk': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tmt_jabatan': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MasaKerjaForm(forms.ModelForm):
    class Meta:
        model = MasaKerja
        exclude = ['dosen', 'tanggal_update']
        widgets = {f: forms.NumberInput(attrs={'class': 'form-control'}) for f in [
            'cpns_tahun', 'cpns_bulan', 'golongan_tahun', 'golongan_bulan',
            'jabatan_tahun', 'jabatan_bulan', 'keseluruhan_tahun', 'keseluruhan_bulan',
            'pensiun_tahun', 'pensiun_bulan'
        ]}


class FakultasForm(forms.ModelForm):
    class Meta:
        model = Fakultas
        fields = '__all__'
        widgets = {
            'kode': forms.TextInput(attrs={'class': 'form-control'}),
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RiwayatStatusDosenForm(forms.ModelForm):
    class Meta:
        model = RiwayatStatusDosen
        exclude = ['dosen']

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

            'keterangan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

class KeluargaDosenForm(forms.ModelForm):
    class Meta:
        model = KeluargaDosen
        exclude = ['dosen', 'created_at']

        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'status_hubungan': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_lahir': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'pekerjaan': forms.TextInput(attrs={'class': 'form-control'}),
        }