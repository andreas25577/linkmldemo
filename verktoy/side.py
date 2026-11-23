"""Bygger nettstedet til GitHub Pages: begrepskart med begrepseiere og «Spør regelverket».
Bruk: python verktoy/side.py [--ut side]"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(__file__))
from repo import Repo
from kontroll import kontroller

def data(r):
    bruk = r.bruk(); feil, adv, dek = kontroller(r)
    B = []
    for i, b in r.begreper.items():
        B.append({'id': i, 'term': b['anbefalt_term']['nb'], 'def': b['definisjon'], 'eier': b['begrepseier'], 'samling': b['samling'],
                  'status': b['status'], 'sensitiv': bool(r.sensitiv(i)),
                  'rel': [[t, m] for t, m in r.relasjoner(b) if t != 'kodeverdi'],
                  'bruk': [[h, w] for h, w in bruk.get(i, [])]})
    E = [{'id': i, 'term': e['term'], 'eier': e['eier'], 'uri': e['uri'], 'bruk': [[h, w] for h, w in bruk.get(i, [])]} for i, e in r.eksterne.items()]
    H = [{'id': h['id'], 'best': h['bestemmelse'], 'url': h['lovdata'], 'type': h['type'], 'avgiver': [r.aktorer[a] for a in h['avgiver']],
          'mottaker': [r.aktorer[a] for a in h['mottaker']], 'formal': h['formal'], 'vilkar': h.get('vilkar', ''),
          'opp': h['opplysninger'], 'saker': h['sakstyper'], 'status': h['status'], 'pres': h.get('presiserer')} for h in r.hjemler]
    S = {n: {'tittel': s['title'], 'sak': (s.get('annotations') or {}).get('sakstype')} for n, s in r.skjemaer.items()}
    Fe = [dict(x, sensitiv=bool(r.sensitiv(x['begrep']) or r.sensitiv(x['rangebegrep']))) for x in r.felt()]
    return {'begreper': B, 'eksterne': E, 'hjemler': H, 'skjemaer': S, 'felt': Fe,
            'eiere': [{'id': i, 'navn': e['navn'], 'github': e['github']} for i, e in r.eiere.items()],
            'kontroll': {'feil': len(feil), 'adv': len(adv), 'dekning': dek}}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--ut', default='side'); a = ap.parse_args()
    r = Repo(); d = data(r); os.makedirs(a.ut, exist_ok=True)
    mal = open(os.path.join(os.path.dirname(__file__), 'side-mal.html'), encoding='utf-8').read()
    open(os.path.join(a.ut, 'index.html'), 'w', encoding='utf-8').write(mal.replace('/*DATA*/null', json.dumps(d, ensure_ascii=False)))
    print('Skrev', a.ut + '/index.html', len(d['begreper']), 'begreper')
