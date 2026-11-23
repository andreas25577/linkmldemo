"""Demosteg 3: Fagenhet for vandel og sikkerhet presiserer definisjonen av straffereaksjon.
Begrepet brukes av andre eiere, modeller og hjemler, så konsekvensanalysen viser hvem som berøres."""
import yaml
p = 'konseptuelt/begreper/vandel-og-sikkerhet.yaml'; s = open(p, encoding='utf-8').read()
d = yaml.safe_load(s); b = next(x for x in d['begreper'] if x['id'] == 'fe:straffereaksjon')
gammel = b['definisjon']
ny = gammel.rstrip('.') + ', også når reaksjonen er ilagt i utlandet'
assert gammel in s
open(p, 'w', encoding='utf-8').write(s.replace(gammel, ny, 1))
print('Ny definisjon:', ny)
