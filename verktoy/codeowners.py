"""Lager .github/CODEOWNERS fra konseptuelt/eiere.yaml, slik at riktig begrepseier må godkjenne endringer.
Bruk: python verktoy/codeowners.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from repo import Repo

def lag_codeowners(r):
    j = r.konfig['jurist']['github']; inf = r.eiere['informasjonsforvaltning']['github']
    l = ['# GENERERT av verktoy/codeowners.py fra konseptuelt/eiere.yaml. Ikke rediger for hånd.',
         '# Den siste regelen som treffer en fil, gjelder.', '',
         f'*  {inf}', f'/konfig/  {inf}', f'/metaskjema/  {inf}', f'/konseptuelt/hjemler/  {j}', '']
    for i, e in r.eiere.items():
        l.append(f'# {e["navn"]}')
        l.append(f'/konseptuelt/begreper/{i}.yaml  {e["github"]}')
    l += ['', '# Logiske skjemaer eies av den som eier hovedbegrepet for sakstypen']
    for n, s in r.skjemaer.items():
        k = next(iter(s.get('classes') or {}), None)
        b = r.klassebegrep(k) if k else None
        e = r.eier_av(b) if b else 'informasjonsforvaltning'
        l.append(f"/{s['_fil']}  {r.eiere[e or 'informasjonsforvaltning']['github']}")
    return '\n'.join(l) + '\n'

if __name__ == '__main__':
    r = Repo(); os.makedirs('.github', exist_ok=True)
    open('.github/CODEOWNERS', 'w', encoding='utf-8').write(lag_codeowners(r)); print(lag_codeowners(r))
