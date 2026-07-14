from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
import io
from datetime import date
from django.http import JsonResponse, HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from .models import (
    Tendik, UnitKerja,
    RiwayatKepangkatanTendik, RiwayatJabatanFungsionalTendik,
    JabatanStrukturalTendik, RiwayatPendidikanTendik,
    TugasTambahanTendik,
)
from .forms import (
    TendikForm, UnitKerjaForm,
    RiwayatKepangkatanTendikForm, RiwayatJabatanFungsionalTendikForm,
    JabatanStrukturalTendikForm, RiwayatPendidikanTendikForm,
    TugasTambahanTendikForm,
)


def is_admin(user):
    return user.is_staff or user.is_superuser


# ─── DASHBOARD TENDIK ─────────────────────────────────────────────────────────

@login_required
def dashboard_tendik(request):
    search      = request.GET.get('q', '')
    unit_id     = request.GET.get('unit', '')
    status_f    = request.GET.get('status', '')
    jabatan_f   = request.GET.get('jabatan', '')

    # ── nama_lengkap adalah @property, tidak bisa di-filter ORM langsung
    # ── gunakan nama_terang untuk search di DB, nama_lengkap untuk tampilan
    qs = Tendik.objects.select_related('unit_kerja').prefetch_related(
        'riwayat_kepangkatan',
        'riwayat_jabatan_fungsional',
        'jabatan_struktural',
        'tugas_tambahan',
    )

    if search:
        qs = qs.filter(
            Q(nama_terang__icontains=search) |  
            Q(nip__icontains=search)            |
            Q(gelar_belakang__icontains=search) |
            Q(gelar_depan__icontains=search)
        )
    if unit_id:
        qs = qs.filter(unit_kerja_id=unit_id)
    if status_f:
        qs = qs.filter(status=status_f)

    rows = []
    no = 1
    for t in qs:
        kp = t.kepangkatan_terakhir
        jf = t.jabatan_fungsional_terakhir
        js = t.jabatan_struktural_aktif
        tt = t.tugas_tambahan_aktif

        if jabatan_f:
            jf_match = jf and jabatan_f.lower() in (jf.nama_jabatan + ' ' + jf.jenjang).lower()
            js_match = js and jabatan_f.lower() in js.jabatan.lower()
            if not (jf_match or js_match):
                continue

        # [FIX] masa_kerja sudah jadi @property di Tendik, tidak ada model terpisah
        mk_k = t.masa_kerja_keseluruhan   # (tahun, bulan)
        mk_g = t.masa_kerja_golongan       # (tahun, bulan)
        mk_j = t.masa_kerja_jabatan        # (tahun, bulan)
        mk_p = t.masa_kerja_pensiun        # (tahun, bulan) — sisa

        rows.append({
            'no': no,
            'tendik': t,
            'kepangkatan': kp,
            'jabatan_fungsional': jf,
            'jabatan_struktural': js,
            'tugas_tambahan': tt,
            # masa kerja sebagai tuple (thn, bln) langsung dari property
            'mk_keseluruhan': mk_k,
            'mk_golongan':    mk_g,
            'mk_jabatan':     mk_j,
            'mk_pensiun':     mk_p,
            'sisa_mk_str':    t.sisa_masa_kerja_str,
        })
        no += 1

    per_page = int(request.GET.get('per_page', 10))
    if per_page > 9000:
        per_page = max(len(rows), 1)
    paginator = Paginator(rows, per_page or 10)
    page_obj  = paginator.get_page(request.GET.get('page'))

    # Stats
    total       = Tendik.objects.count()
    pns_count   = Tendik.objects.filter(status='PNS').count()
    cpns_count  = Tendik.objects.filter(status='CPNS').count()
    pppk_count  = Tendik.objects.filter(status='PPPK').count()
    by_unit     = UnitKerja.objects.annotate(jumlah=Count('tendik')).filter(jumlah__gt=0).order_by('-jumlah')

    context = {
        'page_obj':      page_obj,
        'per_page':      str(per_page),
        'total_tendik':  total,
        'pns_count':     pns_count,
        'cpns_count':    cpns_count,
        'pppk_count':    pppk_count,
        'by_unit':       by_unit,
        'unit_list':     UnitKerja.objects.all().order_by('nama'),
        'search':        search,
        'unit_id':       unit_id,
        'status_filter': status_f,
        'jabatan_filter': jabatan_f,
        'is_admin':      is_admin(request.user),
    }
    return render(request, 'tendik/dashboard_tendik.html', context)


# ─── EXPORT EXCEL ─────────────────────────────────────────────────────────────

@login_required
def export_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Data Tendik"

    # ── Styles ──────────────────────────────────────────────────────────────
    hdr_font = Font(name="Arial", bold=True, color="FFFFFF", size=9)
    hdr_fill = PatternFill("solid", start_color="1F4E79")
    sub_fill = PatternFill("solid", start_color="374151")
    sub_font = Font(name="Arial", bold=True, color="FFFFFF", size=8)
    alt_fill = PatternFill("solid", start_color="EBF3FB")
    center   = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left     = Alignment(horizontal="left",   vertical="center", wrap_text=True)
    thin     = Side(style="thin", color="BFBFBF")
    border   = Border(left=thin, right=thin, top=thin, bottom=thin)

    def hcell(row, col, value):
        c = ws.cell(row=row, column=col, value=value)
        c.font = hdr_font; c.fill = hdr_fill
        c.alignment = center; c.border = border
        return c

    def scell(row, col, value):
        c = ws.cell(row=row, column=col, value=value)
        c.font = sub_font; c.fill = sub_fill
        c.alignment = center; c.border = border
        return c

    # ── Baris 1: Judul ──────────────────────────────────────────────────────
    TOTAL_COLS = 34
    ws.merge_cells(f"A1:{get_column_letter(TOTAL_COLS)}1")
    tc = ws["A1"]
    tc.value     = "DATA TENAGA KEPENDIDIKAN UNIVERSITAS TADULAKO"
    tc.font      = Font(name="Arial", bold=True, size=14, color="1F4E79")
    tc.alignment = center
    ws.row_dimensions[1].height = 28

    # ── Layout kolom ────────────────────────────────────────────────────────
    # Kolom tunggal (merge row 2-3)
    single_cols = {
        1:  ("NO",               6),
        2:  ("NIP",             20),
        3:  ("NAMA",            32),
        4:  ("UNIT KERJA",      20),
        5:  ("STATUS",          10),
        6:  ("L/P",              6),
        7:  ("PANGKAT",         20),
        8:  ("GOL.",             8),
        9:  ("TMT",             13),
        10: ("JAB. FUNGSIONAL", 28),
        11: ("JAB. STRUKTURAL", 24),
        12: ("ESELON",           9),
        23: ("BAGIAN",          20),
        24: ("KARPEG",          14),
        25: ("TMT CPNS",        13),
        26: ("TMT PNS",         13),
        27: ("AGAMA",           12),
        28: ("KEPAKARAN",       22),
        29: ("IJ. BKN",         10),
        30: ("IJ. BORANG",      11),
        31: ("TMP LAHIR",       16),
        32: ("TGL LAHIR",       13),
        33: ("USIA",             7),
        34: ("PENSIUN",          9),
    }
    # Kolom grup (row 2 = label, row 3 = Thn | Bln)
    grouped_cols = {
        13: "MK GOL",
        15: "MK JAB",
        17: "MK KESELURUHAN",
        19: "MK PENSIUN (SISA)",
        # [FIX] Hapus MK CPNS karena sudah jadi @property, bukan field DB
        # Geser agar tetap 34 kolom total
    }
    # [FIX] Kolom 21-22 dipakai untuk TMT PENSIUN + SISA MK (string)
    single_cols[21] = ("TMT PENSIUN", 14)
    single_cols[22] = ("SISA MK",     14)

    for col, (label, width) in single_cols.items():
        ws.merge_cells(start_row=2, start_column=col, end_row=3, end_column=col)
        hcell(2, col, label)
        ws.column_dimensions[get_column_letter(col)].width = width

    for start_col, label in grouped_cols.items():
        ws.merge_cells(start_row=2, start_column=start_col,
                       end_row=2,   end_column=start_col + 1)
        hcell(2, start_col, label)
        scell(3, start_col,     "Thn")
        scell(3, start_col + 1, "Bln")
        ws.column_dimensions[get_column_letter(start_col)].width     = 7
        ws.column_dimensions[get_column_letter(start_col + 1)].width = 7

    ws.row_dimensions[2].height = 38
    ws.row_dimensions[3].height = 18
    ws.freeze_panes = "A4"

    # ── Data rows ────────────────────────────────────────────────────────────
    qs = (
        Tendik.objects
        .select_related("unit_kerja")
        .prefetch_related(
            "riwayat_kepangkatan",
            "riwayat_jabatan_fungsional",
            "jabatan_struktural",
        )
        .order_by("nama_terang")  # [FIX] order by nama_terang bukan nama_lengkap
    )

    def fmt_date(d):
        return d.strftime("%d-%m-%Y") if d else "-"

    def vd(v):
        return v if v else "-"

    center_cols = {0, 5, 7, 8, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 32, 33}

    for row_num, t in enumerate(qs, start=1):
        row_idx = row_num + 3
        fill    = alt_fill if row_num % 2 == 0 else None

        kp  = t.kepangkatan_terakhir
        jf  = t.jabatan_fungsional_terakhir
        js  = t.jabatan_struktural_aktif

        # [FIX] masa_kerja dari @property, bukan model MasaKerjaTendik
        mk_g = t.masa_kerja_golongan       # (thn, bln)
        mk_j = t.masa_kerja_jabatan        # (thn, bln)
        mk_k = t.masa_kerja_keseluruhan    # (thn, bln)
        mk_p = t.masa_kerja_pensiun        # (thn, bln) sisa

        # [FIX] jabatan fungsional: tampilkan nama_dan_jenjang, bukan jenjang saja
        jabf_str = jf.nama_dan_jenjang if jf else "-"

        row_data = [
            # 1-12
            row_num,
            vd(t.nip),
            t.nama_lengkap,              # @property — aman untuk nilai cell
            t.nama_unit,                 # @property
            t.get_status_display(),
            t.jenis_kelamin,
            kp.pangkat   if kp else "-",
            kp.golongan  if kp else "-",
            fmt_date(kp.tmt) if kp else "-",
            jabf_str,                    # [FIX] nama + jenjang
            js.jabatan   if js else "-",
            vd(js.eselon) if js else "-",
            # 13-14 MK GOL
            mk_g[0], mk_g[1],
            # 15-16 MK JAB
            mk_j[0], mk_j[1],
            # 17-18 MK KESELURUHAN
            mk_k[0], mk_k[1],
            # 19-20 MK PENSIUN (sisa)
            mk_p[0], mk_p[1],
            # 21 TMT PENSIUN, 22 SISA MK STR
            fmt_date(t.tmt_pensiun),     # @property
            t.sisa_masa_kerja_str,       # @property
            # 23-34
            vd(t.bagian),
            vd(t.karpeg),
            fmt_date(t.tmt_cpns),
            fmt_date(t.tmt_pns),
            vd(t.agama),
            vd(t.bidang_keahlian),
            vd(t.tingkat_ijazah_bkn),
            vd(t.tingkat_ijazah_borang),
            vd(t.tempat_lahir),
            fmt_date(t.tanggal_lahir),
            t.usia_saat_ini or "-",      # @property
            t.tahun_pensiun or "-",      # @property
        ]

        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font      = Font(name="Arial", size=9)
            cell.alignment = center if (col_idx - 1) in center_cols else left
            cell.border    = border
            if fill:
                cell.fill = fill

        ws.row_dimensions[row_idx].height = 18

    # ── Response ─────────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="Data_Tendik_UNTAD.xlsx"'
    return response


# ─── DETAIL TENDIK ────────────────────────────────────────────────────────────

@login_required
def tendik_detail(request, pk):
    tendik = get_object_or_404(
        Tendik.objects.select_related('unit_kerja').prefetch_related(
            'riwayat_kepangkatan',
            'riwayat_jabatan_fungsional',
            'jabatan_struktural',
            'riwayat_pendidikan',
            'tugas_tambahan',
            # [FIX] tidak ada masa_kerja prefetch — sudah jadi @property
        ),
        pk=pk
    )
    return render(request, 'tendik/tendik_detail.html', {
        'tendik': tendik,
        'is_admin': is_admin(request.user),
        # Kirim tuple masa kerja ke template agar mudah diakses
        'mk_keseluruhan': tendik.masa_kerja_keseluruhan,
        'mk_golongan':    tendik.masa_kerja_golongan,
        'mk_jabatan':     tendik.masa_kerja_jabatan,
        'mk_pensiun':     tendik.masa_kerja_pensiun,
    })


# ─── TENDIK CRUD ──────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def tendik_create(request):
    if request.method == 'POST':
        form = TendikForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'Data tendik {obj.nama_lengkap} berhasil disimpan.')
            return redirect('tendik_detail', pk=obj.pk)
    else:
        form = TendikForm()
    return render(request, 'tendik/tendik_form.html', {
        'form': form, 'title': 'Tambah Tendik Baru'
    })


@login_required
@user_passes_test(is_admin)
def tendik_edit(request, pk):
    tendik = get_object_or_404(Tendik, pk=pk)
    if request.method == 'POST':
        form = TendikForm(request.POST, instance=tendik)
        if form.is_valid():
            form.save()
            messages.success(request, f'Data {tendik.nama_lengkap} berhasil diperbarui.')
            return redirect('tendik_detail', pk=tendik.pk)
    else:
        form = TendikForm(instance=tendik)
    return render(request, 'tendik/tendik_form.html', {
        'form': form, 'tendik': tendik,
        'title': f'Edit: {tendik.nama_lengkap}'
    })


@login_required
@user_passes_test(is_admin)
def tendik_delete(request, pk):
    tendik = get_object_or_404(Tendik, pk=pk)
    if request.method == 'POST':
        nama = tendik.nama_lengkap
        tendik.delete()
        messages.success(request, f'Data tendik {nama} berhasil dihapus.')
        return redirect('dashboard_tendik')
    return render(request, 'tendik/confirm_delete_tendik.html', {
        'obj': tendik, 'title': 'Hapus Tendik'
    })


# ─── KEPANGKATAN ──────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def kepangkatan_tendik_add(request, tendik_pk):
    tendik = get_object_or_404(Tendik, pk=tendik_pk)
    if request.method == 'POST':
        form = RiwayatKepangkatanTendikForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tendik = tendik
            obj.save()
            messages.success(request, 'Riwayat kepangkatan ditambahkan.')
            return redirect('tendik_detail', pk=tendik_pk)
    else:
        form = RiwayatKepangkatanTendikForm()
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': tendik, 'title': 'Tambah Riwayat Kepangkatan'
    })


@login_required
@user_passes_test(is_admin)
def kepangkatan_tendik_edit(request, pk):
    obj = get_object_or_404(RiwayatKepangkatanTendik, pk=pk)
    if request.method == 'POST':
        form = RiwayatKepangkatanTendikForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Riwayat kepangkatan diperbarui.')
            return redirect('tendik_detail', pk=obj.tendik_id)
    else:
        form = RiwayatKepangkatanTendikForm(instance=obj)
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': obj.tendik, 'title': 'Edit Riwayat Kepangkatan'
    })


@login_required
@user_passes_test(is_admin)
def kepangkatan_tendik_delete(request, pk):
    obj = get_object_or_404(RiwayatKepangkatanTendik, pk=pk)
    tendik_pk = obj.tendik_id
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Dihapus.')
        return redirect('tendik_detail', pk=tendik_pk)
    return render(request, 'tendik/confirm_delete_tendik.html', {
        'obj': obj, 'title': 'Hapus Kepangkatan'
    })


# ─── JABATAN FUNGSIONAL ───────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def jabatan_tendik_add(request, tendik_pk):
    tendik = get_object_or_404(Tendik, pk=tendik_pk)
    if request.method == 'POST':
        form = RiwayatJabatanFungsionalTendikForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tendik = tendik
            obj.save()
            messages.success(request, 'Riwayat jabatan fungsional ditambahkan.')
            return redirect('tendik_detail', pk=tendik_pk)
    else:
        form = RiwayatJabatanFungsionalTendikForm()
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': tendik, 'title': 'Tambah Jabatan Fungsional'
    })


@login_required
@user_passes_test(is_admin)
def jabatan_tendik_edit(request, pk):
    obj = get_object_or_404(RiwayatJabatanFungsionalTendik, pk=pk)
    if request.method == 'POST':
        form = RiwayatJabatanFungsionalTendikForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Diperbarui.')
            return redirect('tendik_detail', pk=obj.tendik_id)
    else:
        form = RiwayatJabatanFungsionalTendikForm(instance=obj)
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': obj.tendik, 'title': 'Edit Jabatan Fungsional'
    })


@login_required
@user_passes_test(is_admin)
def jabatan_tendik_delete(request, pk):
    obj = get_object_or_404(RiwayatJabatanFungsionalTendik, pk=pk)
    tendik_pk = obj.tendik_id
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Dihapus.')
        return redirect('tendik_detail', pk=tendik_pk)
    return render(request, 'tendik/confirm_delete_tendik.html', {
        'obj': obj, 'title': 'Hapus Jabatan Fungsional'
    })


# ─── JABATAN STRUKTURAL ───────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def jabatan_struktural_add(request, tendik_pk):
    tendik = get_object_or_404(Tendik, pk=tendik_pk)
    if request.method == 'POST':
        form = JabatanStrukturalTendikForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tendik = tendik
            obj.save()
            messages.success(request, 'Jabatan struktural ditambahkan.')
            return redirect('tendik_detail', pk=tendik_pk)
    else:
        form = JabatanStrukturalTendikForm()
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': tendik, 'title': 'Tambah Jabatan Struktural'
    })


@login_required
@user_passes_test(is_admin)
def jabatan_struktural_edit(request, pk):
    obj = get_object_or_404(JabatanStrukturalTendik, pk=pk)
    if request.method == 'POST':
        form = JabatanStrukturalTendikForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Diperbarui.')
            return redirect('tendik_detail', pk=obj.tendik_id)
    else:
        form = JabatanStrukturalTendikForm(instance=obj)
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': obj.tendik, 'title': 'Edit Jabatan Struktural'
    })


@login_required
@user_passes_test(is_admin)
def jabatan_struktural_delete(request, pk):
    obj = get_object_or_404(JabatanStrukturalTendik, pk=pk)
    tendik_pk = obj.tendik_id
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Dihapus.')
        return redirect('tendik_detail', pk=tendik_pk)
    return render(request, 'tendik/confirm_delete_tendik.html', {
        'obj': obj, 'title': 'Hapus Jabatan Struktural'
    })


# ─── PENDIDIKAN ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def pendidikan_tendik_add(request, tendik_pk):
    tendik = get_object_or_404(Tendik, pk=tendik_pk)
    if request.method == 'POST':
        form = RiwayatPendidikanTendikForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tendik = tendik
            obj.save()
            messages.success(request, 'Riwayat pendidikan ditambahkan.')
            return redirect('tendik_detail', pk=tendik_pk)
    else:
        form = RiwayatPendidikanTendikForm()
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': tendik, 'title': 'Tambah Riwayat Pendidikan'
    })


@login_required
@user_passes_test(is_admin)
def pendidikan_tendik_delete(request, pk):
    obj = get_object_or_404(RiwayatPendidikanTendik, pk=pk)
    tendik_pk = obj.tendik_id
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Dihapus.')
        return redirect('tendik_detail', pk=tendik_pk)
    return render(request, 'tendik/confirm_delete_tendik.html', {
        'obj': obj, 'title': 'Hapus Pendidikan'
    })


# ─── TUGAS TAMBAHAN ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def tugas_tendik_add(request, tendik_pk):
    tendik = get_object_or_404(Tendik, pk=tendik_pk)
    if request.method == 'POST':
        form = TugasTambahanTendikForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tendik = tendik
            obj.save()
            messages.success(request, 'Tugas tambahan ditambahkan.')
            return redirect('tendik_detail', pk=tendik_pk)
    else:
        form = TugasTambahanTendikForm()
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': tendik, 'title': 'Tambah Tugas Tambahan'
    })


@login_required
@user_passes_test(is_admin)
def tugas_tendik_edit(request, pk):
    obj = get_object_or_404(TugasTambahanTendik, pk=pk)
    if request.method == 'POST':
        form = TugasTambahanTendikForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Diperbarui.')
            return redirect('tendik_detail', pk=obj.tendik_id)
    else:
        form = TugasTambahanTendikForm(instance=obj)
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'tendik': obj.tendik, 'title': 'Edit Tugas Tambahan'
    })


@login_required
@user_passes_test(is_admin)
def tugas_tendik_delete(request, pk):
    obj = get_object_or_404(TugasTambahanTendik, pk=pk)
    tendik_pk = obj.tendik_id
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Dihapus.')
        return redirect('tendik_detail', pk=tendik_pk)
    return render(request, 'tendik/confirm_delete_tendik.html', {
        'obj': obj, 'title': 'Hapus Tugas Tambahan'
    })


# ─── UNIT KERJA ──────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def unit_kerja_list(request):
    units = UnitKerja.objects.annotate(jumlah_tendik=Count('tendik')).order_by('nama')
    return render(request, 'tendik/unit_kerja_list.html', {'unit_list': units})


@login_required
@user_passes_test(is_admin)
def unit_kerja_create(request):
    if request.method == 'POST':
        form = UnitKerjaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unit kerja ditambahkan.')
            return redirect('unit_kerja_list')
    else:
        form = UnitKerjaForm()
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'title': 'Tambah Unit Kerja'
    })


@login_required
@user_passes_test(is_admin)
def unit_kerja_edit(request, pk):
    unit = get_object_or_404(UnitKerja, pk=pk)
    if request.method == 'POST':
        form = UnitKerjaForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unit kerja diperbarui.')
            return redirect('unit_kerja_list')
    else:
        form = UnitKerjaForm(instance=unit)
    return render(request, 'tendik/riwayat_form_tendik.html', {
        'form': form, 'title': f'Edit Unit Kerja: {unit.nama}'
    })
    
