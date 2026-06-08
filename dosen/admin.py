from django.contrib import admin
from .models import Dosen, Fakultas, RiwayatKepangkatan, RiwayatJabatanFungsional, RiwayatPendidikan, TugasTambahan, MasaKerja

admin.site.register(Dosen)
admin.site.register(Fakultas)
admin.site.register(RiwayatKepangkatan)
admin.site.register(RiwayatJabatanFungsional)
admin.site.register(RiwayatPendidikan)
admin.site.register(TugasTambahan)
admin.site.register(MasaKerja)
