from django.contrib import admin
from .models import (Tendik, UnitKerja, RiwayatKepangkatanTendik,
    RiwayatJabatanFungsionalTendik, JabatanStrukturalTendik,
    RiwayatPendidikanTendik, TugasTambahanTendik, MasaKerjaTendik)

admin.site.register(Tendik)
admin.site.register(UnitKerja)
admin.site.register(RiwayatKepangkatanTendik)
admin.site.register(RiwayatJabatanFungsionalTendik)
admin.site.register(JabatanStrukturalTendik)
admin.site.register(RiwayatPendidikanTendik)
admin.site.register(TugasTambahanTendik)
admin.site.register(MasaKerjaTendik)
