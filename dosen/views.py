from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone

from .models import (
    Dosen, Fakultas, RiwayatKepangkatan, RiwayatJabatanFungsional,
    RiwayatPendidikan, TugasTambahan, MasaKerja
)
from .forms import (
    DosenForm, RiwayatKepangkatanForm, RiwayatJabatanFungsionalForm,
    RiwayatPendidikanForm, TugasTambahanForm, MasaKerjaForm, FakultasForm
)


def is_admin(user):
    return user.is_staff or user.is_superuser


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Username atau password salah.')
    return render(request, 'dosen/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    search = request.GET.get('q', '')
    fakultas_id = request.GET.get('fakultas', '')
    status_filter = request.GET.get('status', '')
    jabatan_filter = request.GET.get('jabatan', '')

    dosen_qs = Dosen.objects.select_related('fakultas').prefetch_related(
        'riwayat_kepangkatan', 'riwayat_jabatan_fungsional',
        'tugas_tambahan', 'masa_kerja'
    )

    if search:
        dosen_qs = dosen_qs.filter(
            Q(nama_lengkap__icontains=search) |
            Q(nidn__icontains=search) |
            Q(nip__icontains=search) |
            Q(nama_terang__icontains=search)
        )
    if fakultas_id:
        dosen_qs = dosen_qs.filter(fakultas_id=fakultas_id)
    if status_filter:
        dosen_qs = dosen_qs.filter(status=status_filter)

    # Build dashboard rows with latest data
    rows = []
    no = 1
    for d in dosen_qs:
        kp = d.kepangkatan_terakhir
        jf = d.jabatan_fungsional_terakhir
        tt = d.tugas_tambahan_aktif
        mk = getattr(d, 'masa_kerja', None)

        if jabatan_filter and (not jf or jabatan_filter.lower() not in jf.jenjang.lower()):
            continue

        rows.append({
            'no': no,
            'dosen': d,
            'kepangkatan': kp,
            'jabatan_fungsional': jf,
            'tugas_tambahan': tt,
            'masa_kerja': mk,
        })
        no += 1

    paginator = Paginator(rows, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Stats
    total = Dosen.objects.count()
    by_fakultas = Fakultas.objects.annotate(jumlah=Count('dosen')).order_by('-jumlah')
    gb_count = RiwayatJabatanFungsional.objects.filter(
        jenjang__icontains='Guru Besar',
        dosen__in=Dosen.objects.all()
    ).values('dosen').distinct().count()
    lk_count = RiwayatJabatanFungsional.objects.filter(
        jenjang__icontains='Lektor Kepala',
        dosen__in=Dosen.objects.all()
    ).values('dosen').distinct().count()

    context = {
        'page_obj': page_obj,
        'total_dosen': total,
        'by_fakultas': by_fakultas,
        'gb_count': gb_count,
        'lk_count': lk_count,
        'fakultas_list': Fakultas.objects.all(),
        'search': search,
        'fakultas_id': fakultas_id,
        'status_filter': status_filter,
        'jabatan_filter': jabatan_filter,
        'is_admin': is_admin(request.user),
    }
    return render(request, 'dosen/dashboard.html', context)


# ─── DOSEN DETAIL ─────────────────────────────────────────────────────────────

@login_required
def dosen_detail(request, pk):
    dosen = get_object_or_404(Dosen.objects.select_related('fakultas').prefetch_related(
        'riwayat_kepangkatan', 'riwayat_jabatan_fungsional',
        'riwayat_pendidikan', 'tugas_tambahan', 'masa_kerja'
    ), pk=pk)
    context = {
        'dosen': dosen,
        'is_admin': is_admin(request.user),
    }
    return render(request, 'dosen/dosen_detail.html', context)


# ─── DOSEN CRUD (ADMIN ONLY) ──────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def dosen_create(request):
    if request.method == 'POST':
        form = DosenForm(request.POST)
        if form.is_valid():
            dosen = form.save(commit=False)
            dosen.created_by = request.user
            dosen.save()
            messages.success(request, f'Data dosen {dosen.nama_lengkap} berhasil disimpan.')
            return redirect('dosen_detail', pk=dosen.pk)
    else:
        form = DosenForm()
    return render(request, 'dosen/dosen_form.html', {'form': form, 'title': 'Tambah Dosen Baru'})


@login_required
@user_passes_test(is_admin)
def dosen_edit(request, pk):
    dosen = get_object_or_404(Dosen, pk=pk)
    if request.method == 'POST':
        form = DosenForm(request.POST, instance=dosen)
        if form.is_valid():
            form.save()
            messages.success(request, f'Data dosen {dosen.nama_lengkap} berhasil diperbarui.')
            return redirect('dosen_detail', pk=dosen.pk)
    else:
        form = DosenForm(instance=dosen)
    return render(request, 'dosen/dosen_form.html', {
        'form': form, 'dosen': dosen, 'title': f'Edit: {dosen.nama_lengkap}'
    })


@login_required
@user_passes_test(is_admin)
def dosen_delete(request, pk):
    dosen = get_object_or_404(Dosen, pk=pk)
    if request.method == 'POST':
        nama = dosen.nama_lengkap
        dosen.delete()
        messages.success(request, f'Data dosen {nama} berhasil dihapus.')
        return redirect('dashboard')
    return render(request, 'dosen/confirm_delete.html', {'obj': dosen, 'title': 'Hapus Dosen'})


# ─── RIWAYAT KEPANGKATAN ──────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def kepangkatan_add(request, dosen_pk):
    dosen = get_object_or_404(Dosen, pk=dosen_pk)
    if request.method == 'POST':
        form = RiwayatKepangkatanForm(request.POST)
        if form.is_valid():
            riwayat = form.save(commit=False)
            riwayat.dosen = dosen
            riwayat.save()
            messages.success(request, 'Riwayat kepangkatan berhasil ditambahkan.')
            return redirect('dosen_detail', pk=dosen_pk)
    else:
        form = RiwayatKepangkatanForm()
    return render(request, 'dosen/riwayat_form.html', {
        'form': form, 'dosen': dosen, 'title': 'Tambah Riwayat Kepangkatan'
    })


@login_required
@user_passes_test(is_admin)
def kepangkatan_edit(request, pk):
    riwayat = get_object_or_404(RiwayatKepangkatan, pk=pk)
    if request.method == 'POST':
        form = RiwayatKepangkatanForm(request.POST, instance=riwayat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Riwayat kepangkatan berhasil diperbarui.')
            return redirect('dosen_detail', pk=riwayat.dosen_id)
    else:
        form = RiwayatKepangkatanForm(instance=riwayat)
    return render(request, 'dosen/riwayat_form.html', {
        'form': form, 'dosen': riwayat.dosen, 'title': 'Edit Riwayat Kepangkatan'
    })


@login_required
@user_passes_test(is_admin)
def kepangkatan_delete(request, pk):
    riwayat = get_object_or_404(RiwayatKepangkatan, pk=pk)
    dosen_pk = riwayat.dosen_id
    if request.method == 'POST':
        riwayat.delete()
        messages.success(request, 'Riwayat kepangkatan dihapus.')
        return redirect('dosen_detail', pk=dosen_pk)
    return render(request, 'dosen/confirm_delete.html', {'obj': riwayat, 'title': 'Hapus Kepangkatan'})


# ─── RIWAYAT JABATAN FUNGSIONAL ───────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def jabatan_add(request, dosen_pk):
    dosen = get_object_or_404(Dosen, pk=dosen_pk)
    if request.method == 'POST':
        form = RiwayatJabatanFungsionalForm(request.POST)
        if form.is_valid():
            riwayat = form.save(commit=False)
            riwayat.dosen = dosen
            riwayat.save()
            messages.success(request, 'Riwayat jabatan fungsional berhasil ditambahkan.')
            return redirect('dosen_detail', pk=dosen_pk)
    else:
        form = RiwayatJabatanFungsionalForm()
    return render(request, 'dosen/riwayat_form.html', {
        'form': form, 'dosen': dosen, 'title': 'Tambah Riwayat Jabatan Fungsional'
    })


@login_required
@user_passes_test(is_admin)
def jabatan_edit(request, pk):
    riwayat = get_object_or_404(RiwayatJabatanFungsional, pk=pk)
    if request.method == 'POST':
        form = RiwayatJabatanFungsionalForm(request.POST, instance=riwayat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Riwayat jabatan fungsional berhasil diperbarui.')
            return redirect('dosen_detail', pk=riwayat.dosen_id)
    else:
        form = RiwayatJabatanFungsionalForm(instance=riwayat)
    return render(request, 'dosen/riwayat_form.html', {
        'form': form, 'dosen': riwayat.dosen, 'title': 'Edit Jabatan Fungsional'
    })


@login_required
@user_passes_test(is_admin)
def jabatan_delete(request, pk):
    riwayat = get_object_or_404(RiwayatJabatanFungsional, pk=pk)
    dosen_pk = riwayat.dosen_id
    if request.method == 'POST':
        riwayat.delete()
        messages.success(request, 'Riwayat jabatan fungsional dihapus.')
        return redirect('dosen_detail', pk=dosen_pk)
    return render(request, 'dosen/confirm_delete.html', {'obj': riwayat, 'title': 'Hapus Jabatan Fungsional'})


# ─── RIWAYAT PENDIDIKAN ───────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def pendidikan_add(request, dosen_pk):
    dosen = get_object_or_404(Dosen, pk=dosen_pk)
    if request.method == 'POST':
        form = RiwayatPendidikanForm(request.POST)
        if form.is_valid():
            pend = form.save(commit=False)
            pend.dosen = dosen
            pend.save()
            messages.success(request, 'Riwayat pendidikan berhasil ditambahkan.')
            return redirect('dosen_detail', pk=dosen_pk)
    else:
        form = RiwayatPendidikanForm()
    return render(request, 'dosen/riwayat_form.html', {
        'form': form, 'dosen': dosen, 'title': 'Tambah Riwayat Pendidikan'
    })


@login_required
@user_passes_test(is_admin)
def pendidikan_delete(request, pk):
    pend = get_object_or_404(RiwayatPendidikan, pk=pk)
    dosen_pk = pend.dosen_id
    if request.method == 'POST':
        pend.delete()
        messages.success(request, 'Riwayat pendidikan dihapus.')
        return redirect('dosen_detail', pk=dosen_pk)
    return render(request, 'dosen/confirm_delete.html', {'obj': pend, 'title': 'Hapus Riwayat Pendidikan'})


# ─── TUGAS TAMBAHAN ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def tugas_tambahan_add(request, dosen_pk):
    dosen = get_object_or_404(Dosen, pk=dosen_pk)
    if request.method == 'POST':
        form = TugasTambahanForm(request.POST)
        if form.is_valid():
            tt = form.save(commit=False)
            tt.dosen = dosen
            tt.save()
            messages.success(request, 'Tugas tambahan berhasil ditambahkan.')
            return redirect('dosen_detail', pk=dosen_pk)
    else:
        form = TugasTambahanForm()
    return render(request, 'dosen/riwayat_form.html', {
        'form': form, 'dosen': dosen, 'title': 'Tambah Tugas Tambahan'
    })


@login_required
@user_passes_test(is_admin)
def tugas_tambahan_edit(request, pk):
    tt = get_object_or_404(TugasTambahan, pk=pk)
    if request.method == 'POST':
        form = TugasTambahanForm(request.POST, instance=tt)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tugas tambahan berhasil diperbarui.')
            return redirect('dosen_detail', pk=tt.dosen_id)
    else:
        form = TugasTambahanForm(instance=tt)
    return render(request, 'dosen/riwayat_form.html', {
        'form': form, 'dosen': tt.dosen, 'title': 'Edit Tugas Tambahan'
    })


@login_required
@user_passes_test(is_admin)
def tugas_tambahan_delete(request, pk):
    tt = get_object_or_404(TugasTambahan, pk=pk)
    dosen_pk = tt.dosen_id
    if request.method == 'POST':
        tt.delete()
        messages.success(request, 'Tugas tambahan dihapus.')
        return redirect('dosen_detail', pk=dosen_pk)
    return render(request, 'dosen/confirm_delete.html', {'obj': tt, 'title': 'Hapus Tugas Tambahan'})


# ─── MASA KERJA ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def masa_kerja_edit(request, dosen_pk):
    dosen = get_object_or_404(Dosen, pk=dosen_pk)
    mk, _ = MasaKerja.objects.get_or_create(dosen=dosen)
    if request.method == 'POST':
        form = MasaKerjaForm(request.POST, instance=mk)
        if form.is_valid():
            form.save()
            messages.success(request, 'Masa kerja berhasil diperbarui.')
            return redirect('dosen_detail', pk=dosen_pk)
    else:
        form = MasaKerjaForm(instance=mk)
    return render(request, 'dosen/riwayat_form.html', {
        'form': form, 'dosen': dosen, 'title': 'Edit Masa Kerja'
    })


# ─── FAKULTAS MANAGEMENT ──────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def fakultas_list(request):
    fakultas_qs = Fakultas.objects.annotate(jumlah_dosen=Count('dosen')).order_by('nama')
    return render(request, 'dosen/fakultas_list.html', {'fakultas_list': fakultas_qs})


@login_required
@user_passes_test(is_admin)
def fakultas_create(request):
    if request.method == 'POST':
        form = FakultasForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fakultas berhasil ditambahkan.')
            return redirect('fakultas_list')
    else:
        form = FakultasForm()
    return render(request, 'dosen/riwayat_form.html', {'form': form, 'title': 'Tambah Fakultas'})


@login_required
@user_passes_test(is_admin)
def fakultas_edit(request, pk):
    fak = get_object_or_404(Fakultas, pk=pk)
    if request.method == 'POST':
        form = FakultasForm(request.POST, instance=fak)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fakultas berhasil diperbarui.')
            return redirect('fakultas_list')
    else:
        form = FakultasForm(instance=fak)
    return render(request, 'dosen/riwayat_form.html', {'form': form, 'title': f'Edit Fakultas: {fak.nama}'})
