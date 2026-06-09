from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_tendik, name='dashboard_tendik'),
    path('export/excel/', views.export_excel, name='tendik_export_excel'),

    # Tendik CRUD
    path('baru/',        views.tendik_create, name='tendik_create'),
    path('<int:pk>/',    views.tendik_detail, name='tendik_detail'),
    path('<int:pk>/edit/',  views.tendik_edit,   name='tendik_edit'),
    path('<int:pk>/hapus/', views.tendik_delete,  name='tendik_delete'),

    # Kepangkatan
    path('<int:tendik_pk>/kepangkatan/tambah/', views.kepangkatan_tendik_add,    name='kepangkatan_tendik_add'),
    path('kepangkatan/<int:pk>/edit/',          views.kepangkatan_tendik_edit,   name='kepangkatan_tendik_edit'),
    path('kepangkatan/<int:pk>/hapus/',         views.kepangkatan_tendik_delete, name='kepangkatan_tendik_delete'),

    # Jabatan Fungsional
    path('<int:tendik_pk>/jabfung/tambah/', views.jabatan_tendik_add,    name='jabatan_tendik_add'),
    path('jabfung/<int:pk>/edit/',          views.jabatan_tendik_edit,   name='jabatan_tendik_edit'),
    path('jabfung/<int:pk>/hapus/',         views.jabatan_tendik_delete, name='jabatan_tendik_delete'),

    # Jabatan Struktural
    path('<int:tendik_pk>/jabstruk/tambah/', views.jabatan_struktural_add,    name='jabatan_struktural_add'),
    path('jabstruk/<int:pk>/edit/',          views.jabatan_struktural_edit,   name='jabatan_struktural_edit'),
    path('jabstruk/<int:pk>/hapus/',         views.jabatan_struktural_delete, name='jabatan_struktural_delete'),

    # Pendidikan
    path('<int:tendik_pk>/pendidikan/tambah/', views.pendidikan_tendik_add,    name='pendidikan_tendik_add'),
    path('pendidikan/<int:pk>/hapus/',         views.pendidikan_tendik_delete, name='pendidikan_tendik_delete'),

    # Tugas Tambahan
    path('<int:tendik_pk>/tugas/tambah/', views.tugas_tendik_add,    name='tugas_tendik_add'),
    path('tugas/<int:pk>/edit/',          views.tugas_tendik_edit,   name='tugas_tendik_edit'),
    path('tugas/<int:pk>/hapus/',         views.tugas_tendik_delete, name='tugas_tendik_delete'),

    # Masa Kerja
    path('<int:tendik_pk>/masa-kerja/', views.masa_kerja_tendik_edit, name='masa_kerja_tendik_edit'),

    # Unit Kerja
    path('unit-kerja/',          views.unit_kerja_list,   name='unit_kerja_list'),
    path('unit-kerja/baru/',     views.unit_kerja_create, name='unit_kerja_create'),
    path('unit-kerja/<int:pk>/edit/', views.unit_kerja_edit, name='unit_kerja_edit'),
]
