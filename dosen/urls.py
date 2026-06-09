from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
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
]
