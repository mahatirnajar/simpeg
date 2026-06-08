# SIMPEG — Sistem Informasi Kepegawaian
## Universitas Tadulako (UNTAD)
**Framework:** Django 5.2 | **Arsitektur:** Function-Based Views | **Database:** SQLite (siap migrasi ke PostgreSQL)

---

## Modul yang Tersedia

| Modul | Deskripsi |
|-------|-----------|
| **Dosen** | DUK, profil, riwayat kepangkatan, jabatan fungsional, pendidikan, tugas tambahan, masa kerja |
| **Tendik** | DUK, profil, riwayat kepangkatan, jabatan fungsional, **jabatan struktural**, pendidikan, tugas tambahan, masa kerja |
| **Fakultas** | Master data fakultas (dipakai bersama Dosen & Tendik) |
| **Unit Kerja** | Master data unit kerja Tendik (Biro, Bagian, Sub-Bagian, UPT, Lembaga, dll) |

---

## Struktur Proyek
```
kepegawaian_dosen/
├── config/
│   ├── settings.py         # Konfigurasi Django
│   └── urls.py             # Root URL dispatcher
│
├── dosen/                  # App Dosen
│   ├── models.py           # Dosen, Fakultas, RiwayatKepangkatan,
│   │                       # RiwayatJabatanFungsional, RiwayatPendidikan,
│   │                       # TugasTambahan, MasaKerja
│   ├── views.py            # ~30 function-based views
│   ├── forms.py            # ModelForms
│   ├── urls.py             # URL patterns dosen
│   └── management/commands/
│       └── import_duk.py   # Import Excel DUK Dosen
│
├── tendik/                 # App Tendik (BARU)
│   ├── models.py           # Tendik, UnitKerja, RiwayatKepangkatanTendik,
│   │                       # RiwayatJabatanFungsionalTendik,
│   │                       # JabatanStrukturalTendik (khusus tendik),
│   │                       # RiwayatPendidikanTendik,
│   │                       # TugasTambahanTendik, MasaKerjaTendik
│   ├── views.py            # ~35 function-based views
│   ├── forms.py            # ModelForms
│   ├── urls.py             # URL patterns tendik
│   └── management/commands/
│       └── import_tendik.py # Import Excel DUK Tendik
│
└── templates/
    ├── dosen/              # Template halaman Dosen + base.html
    └── tendik/             # Template halaman Tendik
```

---

## Perbedaan Dosen vs Tendik

| Fitur | Dosen | Tendik |
|-------|-------|--------|
| Unit kerja | Fakultas | Unit Kerja (Biro/Bagian/UPT/dll) + bisa di Fakultas |
| Jabatan Fungsional | Guru Besar, Lektor Kepala, Lektor, Asisten Ahli, dst. | Pustakawan, Pranata Komputer, Arsiparis, Analis, dst. |
| **Jabatan Struktural** | ✗ | ✓ (Kepala Biro, Kepala Bagian, Eselon II-IV) |
| No. Reg. Serdos | ✓ | ✗ |
| NIDN | ✓ | ✓ (NIDN/NI) |
| Kepakaran/Bidang Keahlian | ✓ (Ranting Ilmu) | ✓ (Bidang Keahlian) |

---

## Instalasi & Menjalankan

### 1. Persyaratan
```bash
pip install django==5.2 openpyxl
```

### 2. Setup Database
```bash
cd kepegawaian_dosen
python manage.py migrate
```

### 3. Buat Akun Admin
```bash
python manage.py createsuperuser
```

### 4. Import Data dari Excel

**Import Dosen (dari file DUK format lama):**
```bash
python manage.py import_duk /path/ke/DUK_PNS_2026.xlsx
```

**Import Tendik (format kolom sama dengan DUK Dosen):**
```bash
python manage.py import_tendik /path/ke/DUK_Tendik_2026.xlsx
```

> Format kolom Excel yang didukung: NO, NIDN/NI, NUPTK, NIP, NAMA, KODE_UNIT,
> NAMA_UNIT, STATUS, L/P, PANGKAT, GOL, TMT_PANGKAT, JENJANG_JAB, TMT_JAB,
> AK_KUM, MK_CPNS_THN, MK_CPNS_BLN, ... (sama dengan format DUK Dosen)

### 5. Jalankan Server
```bash
python manage.py runserver
```
Akses: **http://127.0.0.1:8000/**

---

## Akun Default (Development)
| Username | Password  | Role   | Keterangan |
|----------|-----------|--------|------------|
| `admin`  | `admin123`| Admin  | Input, edit, hapus semua data |
| `viewer` | `viewer123`| Viewer | Hanya lihat dashboard & profil |

> **⚠️ Ganti password sebelum deploy ke production!**

---

## Peta URL Lengkap

### Autentikasi
| URL | Deskripsi |
|-----|-----------|
| `/` | Login |
| `/logout/` | Logout |

### Dosen
| URL | Akses | Deskripsi |
|-----|-------|-----------|
| `/dashboard/` | Semua | Dashboard DUK Dosen |
| `/dosen/<pk>/` | Semua | Profil + semua riwayat dosen |
| `/dosen/baru/` | Admin | Tambah dosen baru |
| `/dosen/<pk>/edit/` | Admin | Edit data pokok |
| `/dosen/<pk>/hapus/` | Admin | Hapus dosen |
| `/dosen/<pk>/kepangkatan/tambah/` | Admin | Tambah kepangkatan |
| `/dosen/<pk>/jabatan/tambah/` | Admin | Tambah jabatan fungsional |
| `/dosen/<pk>/pendidikan/tambah/` | Admin | Tambah riwayat pendidikan |
| `/dosen/<pk>/tugas/tambah/` | Admin | Tambah tugas tambahan |
| `/dosen/<pk>/masa-kerja/` | Admin | Edit masa kerja |

### Tendik
| URL | Akses | Deskripsi |
|-----|-------|-----------|
| `/tendik/dashboard/` | Semua | Dashboard DUK Tendik |
| `/tendik/<pk>/` | Semua | Profil + semua riwayat tendik |
| `/tendik/baru/` | Admin | Tambah tendik baru |
| `/tendik/<pk>/edit/` | Admin | Edit data pokok |
| `/tendik/<pk>/hapus/` | Admin | Hapus tendik |
| `/tendik/<pk>/kepangkatan/tambah/` | Admin | Tambah kepangkatan |
| `/tendik/<pk>/jabfung/tambah/` | Admin | Tambah jabatan fungsional |
| `/tendik/<pk>/jabstruk/tambah/` | Admin | Tambah jabatan struktural |
| `/tendik/<pk>/pendidikan/tambah/` | Admin | Tambah riwayat pendidikan |
| `/tendik/<pk>/tugas/tambah/` | Admin | Tambah tugas tambahan |
| `/tendik/<pk>/masa-kerja/` | Admin | Edit masa kerja |

### Master Data (Admin)
| URL | Deskripsi |
|-----|-----------|
| `/fakultas/` | Manajemen Fakultas |
| `/tendik/unit-kerja/` | Manajemen Unit Kerja Tendik |

---

## Model Data — Tendik (Baru)

### `UnitKerja`
Menyimpan hierarki unit kerja non-akademik (Biro → Bagian → Sub-Bagian, UPT, Lembaga, dll).
- `kode`, `nama`, `jenis` (REKTORAT/BIRO/BAGIAN/SUB_BAGIAN/UPT/FAKULTAS/LEMBAGA/LAINNYA)
- `induk` → FK ke dirinya sendiri (self-referential, untuk hirarki)

### `Tendik`
Field identitas sama dengan `Dosen`, plus:
- `unit_kerja` → FK ke `UnitKerja`
- `fakultas` → FK ke `Fakultas` (jika tendik ditempatkan di Fakultas)
- `bagian` → teks bebas (Sub-Bagian/bidang dalam unit kerja)
- `bidang_keahlian` → ganti nama dari `ranting_ilmu` dosen

### `JabatanStrukturalTendik` *(hanya ada di Tendik)*
- `jabatan`, `eselon` (II/a s.d. IV/b + Pelaksana), `unit_kerja`, `no_sk`, `tgl_sk`, `tmt_jabatan`, `is_aktif`

---

## Migrasi ke PostgreSQL (Production)
Edit `config/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'simpeg_untad',
        'USER': 'postgres',
        'PASSWORD': 'password_anda',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```
Lalu: `pip install psycopg2-binary`

---

## Saran Pengembangan Lanjutan
1. **Export Excel/PDF** — Cetak DUK ke format Excel/PDF langsung dari browser
2. **Notifikasi Pensiun** — Alert otomatis dosen/tendik yang akan pensiun ≤ 2 tahun
3. **Role per Fakultas/Unit** — Dekan/Kabag hanya bisa lihat data unit sendiri
4. **Kenaikan Pangkat Otomatis** — Reminder pegawai yang sudah waktunya naik pangkat
5. **API REST** — Endpoint JSON untuk integrasi SIAKAD/SIMKEU (Django REST Framework)
6. **Audit Log** — Catat setiap perubahan data + user yang mengubah + timestamp
7. **Laporan Statistik** — Grafik distribusi golongan, jabatan, usia, per fakultas/unit
