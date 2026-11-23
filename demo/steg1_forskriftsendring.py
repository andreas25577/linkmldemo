"""Demosteg 1 (TENKT endring): statsborgerforskriften § 14-8 endres slik at Direktoratet for høyere utdanning og kompetanse
nevnes i stedet for Kompetanse Norge. Endringen er laget for demoen og gjengir ikke en vedtatt forskriftsendring."""
import re
p = 'konseptuelt/hjemler/statsborgerloven.yaml'; s = open(p, encoding='utf-8').read()
blokk = s[s.index('- id: stbf14-8'):]
ny = blokk.replace('  - kompetanse-norge\n', '  - hkdir\n', 1)
ny = re.sub(r'  merknad: Forskriften nevner Kompetanse Norge.*?(?=\n  status:)', '  merknad: Tenkt endring i demoen. Avgiver er endret fra Kompetanse Norge til HK-dir', ny, count=1, flags=re.S)
open(p, 'w', encoding='utf-8').write(s.replace(blokk, ny))
print('Endret', p)
