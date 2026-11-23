"""Engangsskript: konverterer mellomformatet fra prosjektmappen til LinkML-oppsettet i dette repoet.
Bruk: python verktoy/konverter.py <mappe med mellomformat>"""
import sys, os, re, yaml
yaml.Dumper.ignore_aliases = lambda *a: True
SRC = sys.argv[1]
ld = lambda n: yaml.safe_load(open(os.path.join(SRC, n + '.yaml')))
F = ld('felles')
SAK = {'statsborgerskap': 'stb', 'statsborgerskap-melding': 'stbm', 'statsborgerskap-tap': 'stbt'}
C = {n: ld(n) for n in SAK}
H = ld('hjemler-stbl')
BASE = {'fe': 'https://example.org/udi/felles/', 'stb': 'https://example.org/udi/statsborgerskap/',
        'stbm': 'https://example.org/udi/statsborgerskap-melding/', 'stbt': 'https://example.org/udi/statsborgerskap-tap/'}
FB = {b['id']: b for b in F['begreper']}
EXT = dict(F['ekstern'])
for d in C.values():
    for k, v in d['ekstern'].items():
        if not k.startswith('fe-'): EXT.setdefault(k, v)
EXT.update({k: v for k, v in H.get('ekstern', {}).items()})

def ref(v, pre):
    """mellomformat-referanse -> begrep-ID"""
    if v.startswith('ext:fe-'): return 'fe:' + v[7:]
    if v.startswith('ext:'): return v
    if v.startswith('fe:'): return v
    if v.startswith('sak:'):
        _, sak, i = v.split(':'); return SAK[sak] + ':' + i
    return pre + ':' + v

# ---------- hvilke felles begreper og elementer trengs ----------
def refs(x, pre, acc):
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ('til', 'begrep') and isinstance(v, str): acc.add(ref(v, pre))
            else: refs(v, pre, acc)
    elif isinstance(x, list): [refs(v, pre, acc) for v in x]
    return acc
trengs = set()
for n, d in C.items(): refs([d['begreper'], d['modell']], SAK[n], trengs)
for x in H['hjemler']:
    for o in x['opplysninger']: trengs.add(ref(o, 'fe'))
fel_el = set()
for d in C.values(): fel_el |= set(d['modell'].get('felles_elementer', []))
FO = {o['id']: o for o in F['modell']['objekttyper']}
FK = F['modell']['kodelister']; FD = {d['id']: d for d in F['modell'].get('datatyper', [])}
endret = True
while endret:
    endret = False
    for e in list(fel_el):
        o = FO.get(e)
        if not o: continue
        refs(o, 'fe', trengs)
        for p in o['egenskaper']:
            v = p.get('verdi')
            if (v in FO or v in FK or v in FD) and v not in fel_el: fel_el.add(v); endret = True
    for i in [t[3:] for t in list(trengs) if t.startswith('fe:')]:
        b = FB.get(i)
        if not b: continue
        ny = refs(b, 'fe', set()) - trengs
        if ny: trengs |= ny; endret = True
    for k, v in FK.items():
        if k in fel_el and 'fe:' + v not in trengs: trengs.add('fe:' + v); endret = True

# ---------- fiktive begrepseiere ----------
EIERE = [
 {'id': 'informasjonsforvaltning', 'kontakt': 'https://example.org/udi/kontakt/informasjonsforvaltning', 'navn': 'Seksjon for informasjonsforvaltning', 'github': '@andreas25577', 'beskrivelse': 'Fiktiv eier for demoen. Felles grunnbegreper som søknad, vedtak, person og perioder.'},
 {'id': 'vandel-og-sikkerhet', 'kontakt': 'https://example.org/udi/kontakt/vandel-og-sikkerhet', 'navn': 'Fagenhet for vandel og sikkerhet', 'github': '@andreas25577', 'beskrivelse': 'Fiktiv eier for demoen. Straff, politiattest, vandel og nasjonale interesser.'},
 {'id': 'identitet', 'kontakt': 'https://example.org/udi/kontakt/identitet', 'navn': 'Fagenhet for identitet', 'github': '@andreas25577', 'beskrivelse': 'Fiktiv eier for demoen. Identitet, identitetsdokumenter og personopplysninger.'},
 {'id': 'statsborgerskap', 'kontakt': 'https://example.org/udi/kontakt/statsborgerskap', 'navn': 'Fagenhet for statsborgerskap', 'github': '@andreas25577', 'beskrivelse': 'Fiktiv eier for demoen. Søknad og melding om statsborgerskap.'},
 {'id': 'tap-og-tilbakekall', 'kontakt': 'https://example.org/udi/kontakt/tap-og-tilbakekall', 'navn': 'Fagenhet for tap og tilbakekall', 'github': '@andreas25577', 'beskrivelse': 'Fiktiv eier for demoen. Tap, løsning og tilbakekall av statsborgerskap.'},
]
VANDEL = {'politiattest', 'straffereaksjon', 'karenstid', 'vandelsopplysning', 'etterforskningsopplysning', 'grunnleggende-nasjonale-interesser', 'forholdsmessighet'}
IDENT = {'klarlagt-identitet', 'plikt-til-identitetsavklaring', 'personnavn', 'kjonn', 'fodested', 'd-nummer', 'duf-nummer', 'sprak',
         'saerlige-kategorier-personopplysninger', 'biometriske-opplysninger', 'folkeregisteropplysninger', 'statslos', 'mote-og-opplysningsplikt'}
def eier(bid):
    p, i = bid.split(':')
    if p == 'stbt': return 'tap-og-tilbakekall'
    if p in ('stb', 'stbm'): return 'statsborgerskap'
    if i in VANDEL: return 'vandel-og-sikkerhet'
    if i in IDENT: return 'identitet'
    return 'informasjonsforvaltning'

# ---------- begreper ----------
def begrep(b, pre):
    x = {'id': f'{pre}:{b["id"]}', 'anbefalt_term': {'nb': b['nb']}}
    if b.get('nn'): x['anbefalt_term']['nn'] = b['nn']
    if b.get('alt'): x['tillatt_term'] = b['alt']
    x['definisjon'] = b['def']; x['forhold_til_kilde'] = b['forhold']
    if b.get('kilde'): x['kilde'] = b['kilde']
    if b.get('merknad'): x['merknad'] = b['merknad']
    if b.get('opphav'): x['opphav'] = b['opphav']
    x['status'] = b['status']; x['begrepseier'] = eier(x['id']); x['samling'] = {'fe': 'felles', 'stb': 'statsborgerskap', 'stbm': 'statsborgerskap-melding', 'stbt': 'statsborgerskap-tap'}[pre]
    if b.get('verdier'):
        x['kodeverdier'] = [dict({'kode': v['kode'], 'term': v['nb']}, **({'begrep': ref(v['begrep'], pre)} if v.get('begrep') else {})) for v in b['verdier']]
    for r in b.get('rel', []):
        t = ref(r['til'], pre); ty = r['type']
        if ty == 'generisk': x.setdefault('generisk', []).append(t)
        elif ty == 'partitiv': x.setdefault('partitiv', []).append(t)
        elif ty == 'assosiativ': x.setdefault('assosiativ', []).append({'til': t, 'rolle': r.get('rolle', 'har relasjon til')})
        elif ty == 'naer': x.setdefault('naer', []).append(t)
        else: x.setdefault('se_ogsa', []).append(t)
    return x
alle = [begrep(FB[i[3:]], 'fe') for i in sorted(trengs) if i.startswith('fe:') and i[3:] in FB]
for n, d in C.items(): alle += [begrep(b, SAK[n]) for b in d['begreper']]
ider = {b['id'] for b in alle}
# kutt relasjoner til felles begreper som ikke er med i demoen
def gyldig(t): return t.startswith('ext:') and t[4:] in EXT or t in ider
kuttet = 0
for b in alle:
    for k in ('generisk', 'partitiv', 'naer', 'se_ogsa'):
        if k in b:
            f = [t for t in b[k] if gyldig(t)]; kuttet += len(b[k]) - len(f)
            if f: b[k] = f
            else: del b[k]
    if 'assosiativ' in b:
        f = [a for a in b['assosiativ'] if gyldig(a['til'])]; kuttet += len(b['assosiativ']) - len(f)
        if f: b['assosiativ'] = f
        else: del b['assosiativ']
    for v in b.get('kodeverdier', []):
        if 'begrep' in v and not gyldig(v['begrep']): del v['begrep']; kuttet += 1
brukte_ext = set()
def samle(x):
    if isinstance(x, dict): [samle(v) for v in x.values()]
    elif isinstance(x, list): [samle(v) for v in x]
    elif isinstance(x, str) and x.startswith('ext:'): brukte_ext.add(x[4:])
samle(alle)
for x in H['hjemler']:
    for o in x['opplysninger']: samle(ref(o, 'fe'))
for d in [F] + list(C.values()):
    for o in d['modell']['objekttyper']:
        for q in [o] + o['egenskaper']:
            if q.get('begrep'): samle(ref(q['begrep'], 'fe' if d is F else SAK[next(n for n in C if C[n] is d)]))
os.makedirs('konseptuelt/begreper', exist_ok=True); os.makedirs('konseptuelt/hjemler', exist_ok=True)
HODE = '# FORELØPIG UTKAST til demo. Begrepseierne er fiktive. Ikke godkjent faglig eller juridisk.\n'
def skriv(p, d):
    open(p, 'w').write(HODE + yaml.dump(d, allow_unicode=True, sort_keys=False, width=110))
for e in EIERE:
    mine = [b for b in alle if b['begrepseier'] == e['id']]
    skriv(f'konseptuelt/begreper/{e["id"]}.yaml', {'begreper': mine})
skriv('konseptuelt/eiere.yaml', {'eiere': EIERE})
SAML = [{'id': 'felles', 'prefiks': 'fe', 'tittel': {'nb': 'Felles begreper for UDI (utvalg til demo)'}, 'base': BASE['fe']}]
for n, p in SAK.items():
    SAML.append({'id': n, 'prefiks': p, 'tittel': {k: v for k, v in C[n]['meta']['samling'].items()}, 'base': BASE[p]})
skriv('konseptuelt/samlinger.yaml', {'samlinger': SAML})
skriv('konseptuelt/eksterne-begreper.yaml', {'eksterne_begreper': [{'id': 'ext:' + k, 'term': EXT[k]['nb'], 'eier': EXT[k]['eier'], 'uri': EXT[k]['uri']} for k in sorted(brukte_ext)]})

# ---------- hjemler ----------
akt_brukt = {a for x in H['hjemler'] for a in x['avgiver'] + x['mottaker']}
hj = {'lov': H['meta']['lov'], 'lov_uri': H['meta']['lov_uri'], 'forskrift_uri': H['meta']['forskrift_uri'],
      'aktorer': [{'id': k, 'navn': v} for k, v in H['aktorer'].items() if k in akt_brukt], 'hjemler': []}
for x in H['hjemler']:
    y = {k: x[k] for k in ('id', 'bestemmelse', 'lovdata') if k in x}
    if x.get('presiserer'): y['presiserer'] = x['presiserer']
    y.update({'type': x['type'], 'avgiver': x['avgiver'], 'mottaker': x['mottaker'], 'formal': x['formal']})
    if x.get('vilkar'): y['vilkar'] = x['vilkar']
    y['opplysninger'] = [ref(o, 'fe') for o in x['opplysninger']]; y['sakstyper'] = x['sakstyper']
    if x.get('merknad'): y['merknad'] = x['merknad']
    y['status'] = x['status']; hj['hjemler'].append(y)
skriv('konseptuelt/hjemler/statsborgerloven.yaml', hj)

# ---------- logiske modeller ----------
TYPER = {'Tekst': 'string', 'Dato': 'date', 'Boolsk': 'boolean', 'Desimal': 'decimal', 'Heltall': 'integer', 'Belop': 'Belop', 'Varighet': 'Varighet'}
SAERLIG = {'fe:straffereaksjon', 'fe:politiattest', 'fe:vandelsopplysning', 'fe:saerlige-kategorier-personopplysninger', 'fe:biometriske-opplysninger'}
def kurie(bid):
    if bid.startswith('ext:'): return EXT[bid[4:]]['uri']
    return bid
def klassenavn(n): return n
def objekt(o, pre, alle_klasser, alle_enums):
    c = {}
    if o.get('tittel'): c['title'] = o['tittel']
    if o.get('begrep'):
        b = ref(o['begrep'], pre); c['exact_mappings'] = [kurie(b)]
        d = next((x for x in alle if x['id'] == b), None)
        c['description'] = d['definisjon'] if d else (EXT[b[4:]]['nb'] if b.startswith('ext:') else '')
    at = {}
    for p in o['egenskaper']:
        if p['type'] == 'spesialisering': c['is_a'] = p['verdi']; continue
        a = {}
        v = p['verdi']
        if v in TYPER: a['range'] = TYPER[v]
        elif v in alle_enums or v in alle_klasser: a['range'] = v
        else: a['range'] = v
        if p.get('min', 0) >= 1: a['required'] = True
        if str(p.get('maks')) == '*': a['multivalued'] = True
        if p['type'] == 'komposisjon': a['inlined'] = True
        if p['type'] == 'komposisjon' and a.get('multivalued'): a['inlined_as_list'] = True
        if p['type'] == 'rolle': a.setdefault('annotations', {})['egenskapstype'] = 'rolle'
        if p['type'] == 'assosiasjon': a['inlined'] = False
        if p.get('begrep'):
            b = ref(p['begrep'], pre); a['exact_mappings'] = [kurie(b)]
            if b in SAERLIG: a.setdefault('annotations', {})['saerlig_kategori'] = True
        at[p['id']] = a
    c['attributes'] = at
    return c
def enum_fra(navn, bid):
    b = next(x for x in alle if x['id'] == bid)
    e = {'description': b['definisjon'], 'enum_uri': bid, 'permissible_values': {}}
    for v in b.get('kodeverdier', []):
        pv = {'description': v['term']}
        if v.get('begrep'): pv['meaning'] = kurie(v['begrep'])
        e['permissible_values'][v['kode']] = pv
    return e
def skjema(navn, tittel, besk, pre, d, imports, sakstype=None):
    prefixes = {'linkml': 'https://w3id.org/linkml/', 'xsd': 'http://www.w3.org/2001/XMLSchema#'}
    for p, u in BASE.items(): prefixes[p] = u + 'begrep/'
    prefixes['udi'] = f'https://example.org/udi/linkmldemo/logisk/{navn}/'
    s = {'id': f'https://example.org/udi/linkmldemo/logisk/{navn}', 'name': navn, 'title': tittel, 'description': besk,
         'license': 'CC-BY-4.0', 'version': '0.1.0', 'prefixes': prefixes, 'default_prefix': 'udi', 'default_range': 'string', 'imports': imports}
    if sakstype: s['annotations'] = {'sakstype': sakstype}
    return s
# felles
fk = {k: v for k, v in FK.items() if k in fel_el}
klasser = [k for k in fel_el if k in FO] + [k for k in fel_el if k in FD]
fs = skjema('felles', 'Felles modellelementer (utvalg til demo)', 'Felles modellelementer som skjemaene for sakstypene importerer. Utvalget er det statsborgerskap trenger.', 'fe', F, ['linkml:types'])
fs['types'] = {'Belop': {'typeof': 'decimal', 'uri': 'xsd:decimal', 'description': 'Beløp i norske kroner'},
               'Varighet': {'typeof': 'string', 'uri': 'xsd:duration', 'description': 'Varighet etter ISO 8601, for eksempel P7Y'}}
fs['classes'] = {}
for k in sorted(klasser):
    o = FO.get(k) or {'id': k, 'tittel': FD[k].get('tittel'), 'egenskaper': FD[k]['egenskaper']}
    fs['classes'][k] = objekt(o, 'fe', set(FO) | set(FD), set(FK))
fs['enums'] = {k: enum_fra(k, 'fe:' + v) for k, v in sorted(fk.items())}
os.makedirs('logisk', exist_ok=True)
yaml.Dumper.ignore_aliases = lambda *a: True
def skrivs(p, s): open(p, 'w').write('# FORELØPIG UTKAST til demo, generert fra mellomformatet og deretter redigert for hånd.\n' + yaml.dump(s, allow_unicode=True, sort_keys=False, width=110))
skrivs('logisk/felles.yaml', fs)
for n, p in SAK.items():
    d = C[n]; m = d['modell']
    s = skjema(n, d['meta']['modell']['nb'], d['meta'].get('modellbeskrivelse', ''), p, d, ['linkml:types', 'felles'], sakstype=n)
    lokale = {o['id'] for o in m['objekttyper']}
    s['classes'] = {o['id']: objekt(o, p, lokale | set(FO), set(m.get('kodelister', {})) | set(FK)) for o in m['objekttyper']}
    if m.get('kodelister'): s['enums'] = {k: enum_fra(k, ref(v, p)) for k, v in m['kodelister'].items()}
    skrivs(f'logisk/{n}.yaml', s)
print(len(alle), 'begreper', len(brukte_ext), 'eksterne', len(klasser), 'felles klasser', len(fk), 'felles kodelister', kuttet, 'relasjoner kuttet', len(hj['hjemler']), 'hjemler')
