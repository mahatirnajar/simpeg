from django.urls import path
from . import views
from .riwayat_hidup import riwayat_hidup_dosen

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dosen/naik-pangkat/', views.naik_pangkat_list, name='naik_pangkat_list'),
    path('dosen/berhenti/', views.dosen_berhenti_list, name='dosen_berhenti_list'),
    path("dosen/export/excel/", views.export_excel, name="dosen_export_excel"),
    # Dosen CRUD
    path('dosen/baru/', views.dosen_create, name='dosen_create'),
    path('dosen/<int:pk>/', views.dosen_detail, name='dosen_detail'),
    path('dosen/<int:pk>/edit/', views.dosen_edit, name='dosen_edit'),
    path('dosen/<int:pk>/hapus/', views.dosen_delete, name='dosen_delete'),

    # Kepangkatan
    path('dosen/<int:dosen_pk>/kepangkatan/tambah/', views.kepangkatan_add, name='kepangkatan_add'),
    path('kepangkatan/<int:pk>/edit/', views.kepangkatan_edit, name='kepangkatan_edit'),
    path('kepangkatan/<int:pk>/hapus/', views.kepangkatan_delete, name='kepangkatan_delete'),

    # Jabatan Fungsional
    path('dosen/<int:dosen_pk>/jabatan/tambah/', views.jabatan_add, name='jabatan_add'),
    path('jabatan/<int:pk>/edit/', views.jabatan_edit, name='jabatan_edit'),
    path('jabatan/<int:pk>/hapus/', views.jabatan_delete, name='jabatan_delete'),

    # Pendidikan
    path('dosen/<int:dosen_pk>/pendidikan/tambah/', views.pendidikan_add, name='pendidikan_add'),
    path('pendidikan/<int:pk>/hapus/', views.pendidikan_delete, name='pendidikan_delete'),

    # Tugas Tambahan
    path('dosen/<int:dosen_pk>/tugas/tambah/', views.tugas_tambahan_add, name='tugas_tambahan_add'),
    path('tugas/<int:pk>/edit/', views.tugas_tambahan_edit, name='tugas_tambahan_edit'),
    path('tugas/<int:pk>/hapus/', views.tugas_tambahan_delete, name='tugas_tambahan_delete'),

    # Masa Kerja
    path('dosen/<int:dosen_pk>/masa-kerja/', views.masa_kerja_edit, name='masa_kerja_edit'),

    # Fakultas
    path('fakultas/', views.fakultas_list, name='fakultas_list'),
    path('fakultas/baru/', views.fakultas_create, name='fakultas_create'),
    path('fakultas/<int:pk>/edit/', views.fakultas_edit, name='fakultas_edit'),
    
    # Status Dosen
    path('dosen/<int:dosen_id>/status/add/',views.status_dosen_add,name='status_dosen_add'),
    path('status/<int:pk>/edit/',views.status_dosen_edit,name='status_dosen_edit'),
    path('status/<int:pk>/delete/',views.status_dosen_delete,name='status_dosen_delete'),

    # Keluarga
    path('dosen/<int:dosen_id>/keluarga/tambah/', views.keluarga_add, name='keluarga_add'),
    path('keluarga/<int:pk>/edit/', views.keluarga_edit, name='keluarga_edit'),
    path('keluarga/<int:pk>/hapus/', views.keluarga_delete, name='keluarga_delete'),
    
    
    # Riwayat Hidup
    path('dosen/<int:pk>/riwayat-hidup/', riwayat_hidup_dosen, name='dosen_riwayat_hidup'),
]
