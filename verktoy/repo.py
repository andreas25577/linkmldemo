"""Leser hele repoet til ett objekt: begreper, eiere, samlinger, eksterne begreper, hjemler og logiske skjemaer.
Alle verktøyene bygger på dette, så reglene for hvordan filene henger sammen står ett sted."""
import os, glob, yaml
from collections import defaultdict

def _les(p):
    with open(p, encoding='utf-8') as f: return yaml.safe_load(f) or {}

class Repo:
    def __init__(self, rot='.'):
        self.rot = rot
        j = lambda *a: os.path.join(rot, *a)
        self.begreper, self.begrepsfil = {}, {}
        for p in sorted(glob.glob(j('konseptuelt', 'begreper', '*.yaml'))):
            for b in _les(p).get('begreper', []):
                self.begreper[b['id']] = b; self.begrepsfil[b['id']] = os.path.relpath(p, rot)
        self.eiere = {e['id']: e for e in _les(j('konseptuelt', 'eiere.yaml'))['eiere']}
        self.samlinger = {s['id']: s for s in _les(j('konseptuelt', 'samlinger.yaml'))['samlinger']}
        self.eksterne = {e['id']: e for e in _les(j('konseptuelt', 'eksterne-begreper.yaml'))['eksterne_begreper']}
        self.ext_uri = {e['uri']: i for i, e in self.eksterne.items()}
        self.hjemler, self.aktorer, self.hjemmelsfiler = [], {}, {}
        for p in sorted(glob.glob(j('konseptuelt', 'hjemler', '*.yaml'))):
            d = _les(p); self.hjemmelsfiler[os.path.relpath(p, rot)] = d
            self.aktorer.update({a['id']: a['navn'] for a in d['aktorer']})
            for h in d['hjemler']: self.hjemler.append(dict(h, _fil=os.path.relpath(p, rot), _lov=d['lov']))
        self.skjemaer = {}
        for p in sorted(glob.glob(j('logisk', '*.yaml'))):
            s = _les(p); s['_fil'] = os.path.relpath(p, rot); self.skjemaer[s['name']] = s
        self.konfig = _les(j('konfig', 'kontroll.yaml'))

    # ---------- oppslag ----------
    def begrep_id(self, m):
        """exact_mapping/meaning (CURIE eller full URI) -> begrep-ID i repoet, eller None"""
        if m in self.begreper or m in self.eksterne: return m
        if m in self.ext_uri: return self.ext_uri[m]
        return None
    def finnes(self, i): return i in self.begreper or i in self.eksterne
    def term(self, i):
        if i in self.begreper: return self.begreper[i]['anbefalt_term']['nb']
        if i in self.eksterne: return self.eksterne[i]['term']
        return i
    def eier_av(self, i):
        b = self.begreper.get(i); return b['begrepseier'] if b else None
    def relasjoner(self, b):
        """(type, mål) for alle relasjoner fra et begrep"""
        for k in ('generisk', 'partitiv', 'naer', 'se_ogsa'):
            for t in b.get(k, []): yield k, t
        for a in b.get('assosiativ', []): yield 'assosiativ', a['til']
        for v in b.get('kodeverdier', []):
            if v.get('begrep'): yield 'kodeverdi', v['begrep']
    def overbegreper(self, i):
        """begrepet selv og alle generiske overbegreper (transitivt)"""
        sett, kø = [], [i]
        while kø:
            x = kø.pop(0)
            if x in sett: continue
            sett.append(x); kø += self.begreper.get(x, {}).get('generisk', [])
        return sett
    def sensitiv(self, i):
        s = set(self.konfig['saerlige_begreper'])
        return next((o for o in self.overbegreper(i) if o in s), None) if i else None

    # ---------- logiske skjemaer ----------
    def klasser(self):
        """(skjemanavn, klassenavn, klasse) for alle klasser i alle skjemaer"""
        for n, s in self.skjemaer.items():
            for k, c in (s.get('classes') or {}).items(): yield n, k, c
    def klasse(self, navn):
        for n, k, c in self.klasser():
            if k == navn: return n, c
        return None, None
    def klassebegrep(self, navn):
        _, c = self.klasse(navn)
        if not c: return None
        for m in c.get('exact_mappings', []): return self.begrep_id(m) or m
        return None
    def felt(self):
        """Ett element per felt: skjema, sakstype, klasse, felt, range, begrep (feltets eget, ellers range-klassens), saerlig-annotasjon"""
        for n, k, c in self.klasser():
            sak = (self.skjemaer[n].get('annotations') or {}).get('sakstype')
            for f, a in (c.get('attributes') or {}).items():
                eget = next((self.begrep_id(m) or m for m in a.get('exact_mappings', [])), None)
                rb = self.klassebegrep(a.get('range')) if a.get('range') else None
                yield {'skjema': n, 'fil': self.skjemaer[n]['_fil'], 'sakstype': sak, 'klasse': k, 'felt': f,
                       'range': a.get('range'), 'begrep': eget, 'rangebegrep': rb,
                       'merket': bool((a.get('annotations') or {}).get('saerlig_kategori'))}
    def enumverdier(self):
        for n, s in self.skjemaer.items():
            for e, d in (s.get('enums') or {}).items():
                yield n, e, d.get('enum_uri'), {k: (v or {}).get('meaning') for k, v in (d.get('permissible_values') or {}).items()}

    # ---------- bruk ----------
    def bruk(self):
        """begrep-ID -> liste av (hva, hvor) som bruker begrepet"""
        u = defaultdict(list)
        for i, b in self.begreper.items():
            for t, m in self.relasjoner(b): u[m].append(('begrep', f'{i} ({t})'))
        for n, k, c in self.klasser():
            for m in c.get('exact_mappings', []): u[self.begrep_id(m) or m].append(('klasse', f'{n}: {k}'))
        for f in self.felt():
            if f['begrep']: u[f['begrep']].append(('felt', f"{f['skjema']}: {f['klasse']}.{f['felt']}"))
            if f['rangebegrep'] and f['rangebegrep'] != f['begrep']: u[f['rangebegrep']].append(('felt', f"{f['skjema']}: {f['klasse']}.{f['felt']} (via {f['range']})"))
        for n, e, uri, vs in self.enumverdier():
            if uri: u[self.begrep_id(uri) or uri].append(('kodeliste', f'{n}: {e}'))
            for k, m in vs.items():
                if m: u[self.begrep_id(m) or m].append(('kodeverdi', f'{n}: {e}.{k}'))
        for h in self.hjemler:
            for o in h['opplysninger']: u[o].append(('hjemmel', f"{h['bestemmelse']} ({h['id']})"))
        return u
