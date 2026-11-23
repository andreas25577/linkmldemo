"""Kontrollene som kjører på hver pull request.
Bruk: python verktoy/kontroll.py [--rapport fil.md]
Avslutter med kode 1 hvis det finnes feil. Advarsler stopper ikke."""
import sys, os, re, argparse
sys.path.insert(0, os.path.dirname(__file__))
from repo import Repo
from codeowners import lag_codeowners

def kontroller(r):
    feil, adv = [], []
    F = lambda regel, hvor, tekst: feil.append((regel, hvor, tekst))
    A = lambda regel, hvor, tekst: adv.append((regel, hvor, tekst))
    pref = {s['prefiks']: s['id'] for s in r.samlinger.values()}
    # 1 Begrepene henger sammen
    for i, b in r.begreper.items():
        f = r.begrepsfil[i]
        if b['begrepseier'] not in r.eiere: F('begrepseier', f, f'{i}: ukjent begrepseier «{b["begrepseier"]}»')
        elif not f.endswith(b['begrepseier'] + '.yaml'): F('begrepseier', f, f'{i}: ligger i feil fil, eieren er {b["begrepseier"]}')
        if b['samling'] not in r.samlinger: F('samling', f, f'{i}: ukjent samling «{b["samling"]}»')
        elif pref.get(i.split(':')[0]) != b['samling']: F('samling', f, f'{i}: prefikset passer ikke med samlingen {b["samling"]}')
        for t, m in r.relasjoner(b):
            if not r.finnes(m): F('referanse', f, f'{i}: {t}-relasjon til {m}, som ikke finnes')
            if m == i: F('referanse', f, f'{i}: relasjon til seg selv')
        term = b['anbefalt_term']['nb'].lower()
        if re.search(r'\b' + re.escape(term) + r'\b', b['definisjon'].lower()): A('definisjon', f, f'{i}: definisjonen bruker termen selv («{term}»)')
        if 'nn' not in b['anbefalt_term']: F('term', f, f'{i}: mangler nynorsk term, som SKOS-AP-NO krever')
        if b['status'] == 'usikker': A('status', f, f'{i}: status usikker, må vurderes av {r.eiere[b["begrepseier"]]["navn"]}')
    # 2 Skjemaene peker på begreper som finnes
    for n, k, c in r.klasser():
        for m in c.get('exact_mappings', []):
            if not r.begrep_id(m): F('begrep i modell', r.skjemaer[n]['_fil'], f'{k}: peker på {m}, som ikke finnes')
    for x in r.felt():
        if x['begrep'] and not r.begrep_id(x['begrep']): F('begrep i modell', x['fil'], f"{x['klasse']}.{x['felt']}: peker på {x['begrep']}, som ikke finnes")
    for n, e, uri, vs in r.enumverdier():
        for k, m in vs.items():
            if m and not r.begrep_id(m): F('begrep i modell', r.skjemaer[n]['_fil'], f'{e}.{k}: peker på {m}, som ikke finnes')
    sakstyper = {(s.get('annotations') or {}).get('sakstype') for s in r.skjemaer.values()} - {None}
    # 3 Hjemlene henger sammen
    hid = {h['id'] for h in r.hjemler}
    for h in r.hjemler:
        hv = f"{h['_fil']} ({h['id']})"
        for o in h['opplysninger']:
            if not r.finnes(o): F('hjemmel', hv, f'opplysningen {o} finnes ikke som begrep')
        for a in h['avgiver'] + h['mottaker']:
            if a not in r.aktorer: F('hjemmel', hv, f'ukjent aktør «{a}»')
        for s in h['sakstyper']:
            if s not in sakstyper: F('hjemmel', hv, f'sakstypen «{s}» har ikke noe logisk skjema')
        if h.get('presiserer') and h['presiserer'] not in hid: F('hjemmel', hv, f"presiserer {h['presiserer']}, som ikke finnes")
    # 4 Kjedekontroll: sensitive felt må ha hjemmel for samme sakstype
    dekning = []
    for x in r.felt():
        kilde = x['begrep'] if x['begrep'] and r.sensitiv(x['begrep']) else (x['rangebegrep'] if r.sensitiv(x['rangebegrep']) else None)
        if not kilde and not x['merket']: continue
        kilde = kilde or x['begrep']
        hvor = f"{x['skjema']}: {x['klasse']}.{x['felt']}"
        if not x['sakstype']:
            continue  # felles-skjemaet arver sakstype fra den som bruker det
        kjede = r.overbegreper(kilde) if kilde else []
        treff = [h for h in r.hjemler if x['sakstype'] in h['sakstyper'] and set(h['opplysninger']) & set(kjede)]
        if not treff:
            F('kjedekontroll', x['fil'], f"{hvor} er sensitivt ({r.term(r.sensitiv(kilde) or kilde)}), men ingen hjemmel for sakstypen «{x['sakstype']}» gir anledning til å innhente eller behandle {r.term(kilde)}")
        else:
            godkjent = [h for h in treff if h['status'] == 'godkjent']
            if not godkjent: A('kjedekontroll', x['fil'], f"{hvor}: dekket av {', '.join(h['bestemmelse'] for h in treff)}, men ingen av hjemlene er juridisk godkjent")
            if not x['merket']: A('kjedekontroll', x['fil'], f"{hvor}: sensitivt felt uten annotasjonen saerlig_kategori")
        dekning.append((hvor, r.term(kilde), [h['bestemmelse'] for h in treff]))
    # 5 CODEOWNERS er i takt med eiere.yaml
    p = os.path.join(r.rot, '.github', 'CODEOWNERS')
    if not os.path.exists(p) or open(p, encoding='utf-8').read() != lag_codeowners(r):
        F('CODEOWNERS', '.github/CODEOWNERS', 'er ikke i takt med konseptuelt/eiere.yaml. Kjør python verktoy/codeowners.py')
    return feil, adv, dekning

def rapport(feil, adv, dekning):
    l = ['## Kontroll av begreper, modeller og hjemler', '']
    l.append(('❌ **%d feil** må rettes før endringen kan flettes.' % len(feil)) if feil else '✅ **Ingen feil.**')
    l.append(f'⚠️ {len(adv)} advarsler.' if adv else '')
    if feil:
        l += ['', '### Feil', '', '| Regel | Fil | Hva |', '|---|---|---|'] + [f'| {a} | `{b}` | {c} |' for a, b, c in feil]
    if dekning:
        l += ['', '### Sensitive felt og hjemlene som dekker dem', '', '| Felt | Opplysning | Hjemmel |', '|---|---|---|']
        l += [f"| `{a}` | {b} | {', '.join(c) if c else '❌ ingen'} |" for a, b, c in dekning]
    if adv:
        grp = {}
        for a, b, c in adv: grp.setdefault(a, []).append(c)
        l += ['', '<details><summary>Advarsler</summary>', '']
        for a, cs in grp.items(): l += [f'**{a}** ({len(cs)})', ''] + [f'- {c}' for c in cs] + ['']
        l += ['</details>']
    return '\n'.join(l) + '\n'

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--rapport'); ap.add_argument('--rot', default='.')
    a = ap.parse_args()
    feil, adv, dek = kontroller(Repo(a.rot)); md = rapport(feil, adv, dek)
    if a.rapport: open(a.rapport, 'w', encoding='utf-8').write(md)
    print(md); sys.exit(1 if feil else 0)
