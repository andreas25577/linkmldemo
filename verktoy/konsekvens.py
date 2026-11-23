"""Konsekvensanalyse for en pull request: hva er endret, hva bruker det, og hvilke begrepseiere må se på det.
Bruk: python verktoy/konsekvens.py <mappe med main> <mappe med endringen> [--rapport fil.md]"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(__file__))
from repo import Repo

FELT = {'anbefalt_term': 'term', 'tillatt_term': 'tillatt term', 'definisjon': 'definisjon', 'status': 'status', 'begrepseier': 'begrepseier',
        'kilde': 'kilde', 'merknad': 'merknad', 'generisk': 'overbegrep', 'partitiv': 'helhet', 'assosiativ': 'assosiative relasjoner',
        'kodeverdier': 'kodeverdier', 'samling': 'samling', 'forhold_til_kilde': 'forhold til kilde', 'naer': 'nærliggende', 'se_ogsa': 'se også'}
HFELT = {'bestemmelse': 'bestemmelse', 'lovdata': 'lenke', 'avgiver': 'avgiver', 'mottaker': 'mottaker', 'formal': 'formål', 'vilkar': 'vilkår',
         'opplysninger': 'opplysninger', 'sakstyper': 'sakstyper', 'status': 'status', 'merknad': 'merknad', 'type': 'type'}

def felt_i(r):
    return {f"{x['skjema']}: {x['klasse']}.{x['felt']}": x for x in r.felt()}

def analyser(a, b):
    endr = []  # (art, id, beskrivelse, berørte begrep-ID-er)
    for i in sorted(set(a.begreper) | set(b.begreper)):
        x, y = a.begreper.get(i), b.begreper.get(i)
        if x == y: continue
        if not x: endr.append(('nytt begrep', i, b.term(i), {i}))
        elif not y: endr.append(('fjernet begrep', i, a.term(i), {i}))
        else:
            hva = [FELT.get(k, k) for k in sorted(set(x) | set(y)) if x.get(k) != y.get(k)]
            endr.append(('endret begrep', i, f"{b.term(i)}: {', '.join(hva)}", {i}))
    ah, bh = {h['id']: h for h in a.hjemler}, {h['id']: h for h in b.hjemler}
    for i in sorted(set(ah) | set(bh)):
        x, y = ah.get(i), bh.get(i)
        if x == y: continue
        h = y or x
        if not x: endr.append(('ny hjemmel', i, h['bestemmelse'], set(h['opplysninger'])))
        elif not y: endr.append(('fjernet hjemmel', i, h['bestemmelse'], set(h['opplysninger'])))
        else:
            hva = [HFELT.get(k, k) for k in sorted(set(x) | set(y)) if not k.startswith('_') and x.get(k) != y.get(k)]
            endr.append(('endret hjemmel', i, f"{h['bestemmelse']}: {', '.join(hva)}", set(x['opplysninger']) | set(y['opplysninger'])))
    af, bf = felt_i(a), felt_i(b)
    for k in sorted(set(af) | set(bf)):
        x, y = af.get(k), bf.get(k)
        if x == y: continue
        z = y or x; beg = {q for q in (z['begrep'], z['rangebegrep']) if q}
        art = 'nytt felt' if not x else 'fjernet felt' if not y else 'endret felt'
        endr.append((art, k, f"range {z['range']}" + (f", begrep {b.term(z['begrep'])}" if z['begrep'] else ''), beg))
    return endr

def rapport(a, b, endr):
    if not endr: return '## Konsekvensanalyse\n\nIngen endringer i begreper, hjemler eller modeller.\n'
    bruk = b.bruk(); l = ['## Konsekvensanalyse', '', f'{len(endr)} endringer. Listen viser hva som bruker det som er endret.', '']
    eiere = set()
    for art, i, tekst, berort in endr:
        l += [f'### {art.capitalize()}: `{i}`', '', tekst, '']
        for q in sorted(berort):
            e = b.eier_av(q) or a.eier_av(q)
            if e: eiere.add(e)
            brukere = bruk.get(q, [])
            if not brukere: l += [f'- **{b.term(q)}** (`{q}`) brukes ikke av noe annet.']; continue
            l += [f'- **{b.term(q)}** (`{q}`), eier {b.eiere.get(e, {}).get("navn", "ekstern")}, brukes av:']
            for hva, hvor in brukere:
                l.append(f'  - {hva}: {hvor}')
                if hva == 'begrep':
                    e2 = b.eier_av(hvor.split(' ')[0])
                    if e2: eiere.add(e2)
                if hva in ('felt', 'klasse', 'kodeliste', 'kodeverdi'):
                    n = hvor.split(':')[0]; sak = (b.skjemaer.get(n, {}).get('annotations') or {}).get('sakstype')
                    if sak: l[-1] += f' (sakstype {sak})'
        if art.endswith('hjemmel'):
            h = next((h for h in b.hjemler + a.hjemler if h['id'] == i))
            berf = [f"{x['skjema']}: {x['klasse']}.{x['felt']}" for x in b.felt() if x['sakstype'] in h['sakstyper'] and ({x['begrep'], x['rangebegrep']} & berort)]
            if berf: l += ['', 'Felt i modellene som bygger på hjemmelen:'] + [f'- `{f}`' for f in berf]
            l += ['', f"⚖️ Hjemmelsendringer skal godkjennes av {b.konfig['jurist']['navn']}."]
        l.append('')
    l += ['### Begrepseiere som bør se på endringen', ''] + [f"- {b.eiere[e]['navn']} ({b.eiere[e]['github']})" for e in sorted(eiere)]
    l += ['', 'Eierne av filene som er endret, blir bedt om godkjenning automatisk gjennom CODEOWNERS. De andre er varslet her fordi de bruker det som er endret.']
    return '\n'.join(l) + '\n'

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('main'); ap.add_argument('endring'); ap.add_argument('--rapport')
    x = ap.parse_args(); a, b = Repo(x.main), Repo(x.endring); md = rapport(a, b, analyser(a, b))
    if x.rapport: open(x.rapport, 'w', encoding='utf-8').write(md)
    print(md)
