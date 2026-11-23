"""Bygger RDF til data.norge fra repoet og validerer mot SHACL-formene til Digdir.
  bygg/begreper-<samling>.ttl            SKOS-AP-NO-Begrep
  bygg/informasjonsmodell-<skjema>.ttl   ModellDCAT-AP-NO
  bygg/hjemler-<lov>.ttl                 DPV og ELI
Bruk: python verktoy/rdf.py [--uten-shacl]"""
import sys, os, re, yaml, argparse, collections, warnings
warnings.filterwarnings('ignore', message='Code: (min|max)Occurs')
sys.path.insert(0, os.path.dirname(__file__))
from repo import Repo
from rdflib import Graph, Namespace, URIRef, Literal, BNode, RDF, RDFS, XSD
from rdflib.namespace import SKOS, DCTERMS as DCT, DCAT, FOAF

MD = Namespace('https://data.norge.no/vocabulary/modelldcatno#'); SN = Namespace('https://data.norge.no/vocabulary/skosno#')
EU = Namespace('http://publications.europa.eu/ontology/euvoc#'); XK = Namespace('http://rdf-vocabulary.ddialliance.org/xkos#')
VC = Namespace('http://www.w3.org/2006/vcard/ns#'); ORG = Namespace('http://www.w3.org/ns/org#')
DPV = Namespace('https://w3id.org/dpv#'); ELI = Namespace('http://data.europa.eu/eli/ontology#'); SH = Namespace('http://www.w3.org/ns/shacl#')
RWS = 'https://data.norge.no/vocabulary/relationship-with-source-type#'
UTGIVER = URIRef('https://organization-catalog.fellesdatakatalog.digdir.no/organizations/974760746')
BASE = 'https://example.org/udi/linkmldemo/'
TYPER = {'string': 'string', 'date': 'date', 'boolean': 'boolean', 'integer': 'integer', 'decimal': 'decimal', 'Belop': 'decimal', 'Varighet': 'duration'}

class Bygger:
    def __init__(self, r):
        self.r = r; self.pref = {s['prefiks']: s for s in r.samlinger.values()}
    def uri(self, i):
        if i.startswith('ext:'): return URIRef(self.r.eksterne[i]['uri'])
        if i.startswith('http'): return URIRef(i)
        p, l = i.split(':', 1); return URIRef(self.pref[p]['base'] + 'begrep/' + l)
    def bind(self, g):
        for p, n in [('skos', SKOS), ('dct', DCT), ('dcat', DCAT), ('skosno', SN), ('euvoc', EU), ('xkos', XK), ('vcard', VC),
                     ('modelldcatno', MD), ('dpv', DPV), ('eli', ELI)]: g.bind(p, n)
        for p, s in self.pref.items(): g.bind(p, Namespace(s['base'] + 'begrep/'))
    def kontakt(self, g, s, eier):
        e = self.r.eiere[eier]; c = BNode(); g.add((s, DCAT.contactPoint, c)); g.add((c, RDF.type, VC.Organization))
        g.add((c, VC['organization-name'], Literal(e['navn'], lang='nb'))); g.add((c, VC.hasURL, URIRef(e['kontakt'])))

    def begreper(self, sid):
        r = self.r; sm = r.samlinger[sid]; g = Graph(); self.bind(g)
        col = URIRef(sm['base'] + 'begrepssamling'); g.add((col, RDF.type, SKOS.Collection)); g.add((UTGIVER, RDF.type, ORG.Organization))
        g.add((col, DCT.identifier, Literal(str(col), datatype=XSD.anyURI))); g.add((col, DCT.publisher, UTGIVER)); self.kontakt(g, col, 'informasjonsforvaltning')
        for l, t in sm['tittel'].items(): g.add((col, DCT.title, Literal(t, lang=l)))
        g.add((col, DCT.description, Literal('Foreløpig utkast til demo. Begrepene er ikke godkjent.', lang='nb')))
        for i, b in r.begreper.items():
            if b['samling'] != sid: continue
            s = self.uri(i); g.add((col, SKOS.member, s)); g.add((s, RDF.type, SKOS.Concept))
            for l, t in b['anbefalt_term'].items(): g.add((s, SKOS.prefLabel, Literal(t, lang=l)))
            for t in b.get('tillatt_term', []): g.add((s, SKOS.altLabel, Literal(t, lang='nb')))
            g.add((s, DCT.identifier, Literal(str(s), datatype=XSD.anyURI))); g.add((s, DCT.publisher, UTGIVER))
            self.kontakt(g, s, b['begrepseier'])  # begrepseieren blir kontaktpunkt i data.norge
            x = BNode(); g.add((s, EU.xlDefinition, x)); g.add((x, RDF.type, EU.XlNote)); g.add((x, RDF.value, Literal(b['definisjon'], lang='nb')))
            g.add((x, SN.relationshipWithSource, URIRef(RWS + {'egendefinert': 'self-composed', 'basert': 'derived-from-source', 'sitat': 'direct-from-source'}[b['forhold_til_kilde']])))
            if b.get('kilde'): g.add((x, DCT.source, Literal(b['kilde'], lang='nb')))
            g.add((s, SKOS.scopeNote, Literal(' '.join(filter(None, [b.get('merknad'), f"Status i utkastet: {b['status']}."])), lang='nb')))
            for t in b.get('generisk', []): g.add((s, XK.specializes, self.uri(t)))
            for t in b.get('partitiv', []): g.add((s, XK.isPartOf, self.uri(t)))
            for t in b.get('naer', []): g.add((s, SKOS.closeMatch, self.uri(t)))
            for t in b.get('se_ogsa', []): g.add((s, RDFS.seeAlso, self.uri(t)))
            for a in b.get('assosiativ', []):
                n = BNode(); g.add((s, SN.isFromConceptIn, n)); g.add((n, RDF.type, SN.AssociativeConceptRelation))
                g.add((n, SN.hasToConcept, self.uri(a['til']))); g.add((n, SN.relationRole, Literal(a['rolle'], lang='nb')))
        # omvendte relasjoner innenfor repoet
        for i, b in r.begreper.items():
            for t in b.get('generisk', []):
                if t in r.begreper and r.begreper[t]['samling'] == sid: g.add((self.uri(t), XK.generalizes, self.uri(i)))
            for t in b.get('partitiv', []):
                if t in r.begreper and r.begreper[t]['samling'] == sid: g.add((self.uri(t), XK.hasPart, self.uri(i)))
        return g

    def modell(self, navn):
        r = self.r; sk = r.skjemaer[navn]; g = Graph(); self.bind(g)
        M = Namespace(BASE + 'modell/' + navn + '/'); g.bind('modell', M)
        FM = Namespace(BASE + 'modell/felles/')
        lokale = set(sk.get('classes') or {}) | set(sk.get('enums') or {}) | set(sk.get('types') or {})
        el = lambda n: (M if n in lokale else FM)[n]
        im = URIRef(BASE + 'informasjonsmodell/' + navn); g.add((im, RDF.type, MD.InformationModel)); g.add((im, DCT.publisher, UTGIVER)); g.add((UTGIVER, RDF.type, FOAF.Agent))
        g.add((im, DCT.title, Literal(sk['title'], lang='nb'))); g.add((im, DCT.description, Literal(sk.get('description') or sk['title'], lang='nb')))
        g.add((im, DCT.identifier, Literal(str(im), datatype=XSD.anyURI))); self.kontakt(g, im, 'informasjonsforvaltning')
        def ny(s, typ, tittel, mapping=None):
            g.add((im, MD.containsModelElement, s)); g.add((s, RDF.type, typ)); g.add((s, DCT.title, Literal(tittel, lang='nb')))
            if mapping: g.add((s, DCT.subject, self.uri(r.begrep_id(mapping) or mapping)))
        enkle = set()
        def enkel(t):
            s = M['type-' + t]
            if t not in enkle:
                enkle.add(t); ny(s, MD.SimpleType, t); g.add((s, MD.typeDefinitionReference, Literal(str(XSD) + TYPER[t], datatype=XSD.anyURI)))
            return s
        enums = set(sk.get('enums') or {}) | set(r.skjemaer['felles'].get('enums') or {})
        for n, e in (sk.get('enums') or {}).items():
            cl = M[n]; ny(cl, MD.CodeList, e.get('description') or n, e.get('enum_uri'))
            for k, v in (e.get('permissible_values') or {}).items():
                c = M[n + '-' + k]; g.add((c, RDF.type, MD.CodeElement)); g.add((c, SKOS.inScheme, cl)); g.add((c, SKOS.notation, Literal(k)))
                g.add((c, SKOS.prefLabel, Literal((v or {}).get('description') or k, lang='nb')))
                if (v or {}).get('meaning'): g.add((c, DCT.subject, self.uri(r.begrep_id(v['meaning']) or v['meaning'])))
        for n, c in (sk.get('classes') or {}).items():
            s = M[n]; m = (c.get('exact_mappings') or [None])[0]
            ny(s, MD.ObjectType if m else MD.DataType, c.get('title') or (r.term(r.begrep_id(m)).capitalize() if m else n), m)
            if c.get('is_a'):
                p = M[n + '-spesialisering']; g.add((s, MD.hasProperty, p)); g.add((p, RDF.type, MD.Specialization)); g.add((p, MD.hasGeneralConcept, el(c['is_a'])))
            for f, a in (c.get('attributes') or {}).items():
                p = M[n + '-' + f]; g.add((s, MD.hasProperty, p)); g.add((p, DCT.title, Literal(f, lang='nb'))); rg = a.get('range', 'string')
                fm = (a.get('exact_mappings') or [None])[0]
                if fm: g.add((p, DCT.subject, self.uri(r.begrep_id(fm) or fm)))
                if rg in TYPER: g.add((p, RDF.type, MD.Attribute)); g.add((p, MD.hasSimpleType, enkel(rg) if rg not in ('Belop', 'Varighet') else enkel(rg)))
                elif rg in enums: g.add((p, RDF.type, MD.Attribute)); g.add((p, MD.hasValueFrom, el(rg)))
                else:
                    rb = r.klassebegrep(rg)
                    if not fm and rb: g.add((p, DCT.subject, self.uri(rb)))
                    if (a.get('annotations') or {}).get('egenskapstype') == 'rolle': g.add((p, RDF.type, MD.Role)); g.add((p, MD.hasObjectType, el(rg)))
                    elif a.get('inlined'): g.add((p, RDF.type, MD.Composition)); g.add((p, MD.contains, el(rg)))
                    else: g.add((p, RDF.type, MD.Association)); g.add((p, MD.refersTo, el(rg)))
                g.add((p, XSD['minOccurs'], Literal(1 if a.get('required') else 0, datatype=XSD.nonNegativeInteger)))
                g.add((p, XSD['maxOccurs'], Literal('*') if a.get('multivalued') else Literal(1, datatype=XSD.nonNegativeInteger)))
        return g

    def hjemler(self, fil):
        r = self.r; d = r.hjemmelsfiler[fil]; g = Graph(); self.bind(g)
        ms = yaml.safe_load(open(os.path.join(r.rot, 'metaskjema', 'hjemmel.yaml'), encoding='utf-8'))
        typer = {k: v['meaning'].split(':')[1] for k, v in ms['enums']['Hjemmeltype']['permissible_values'].items()}
        n = os.path.splitext(os.path.basename(fil))[0]
        H = Namespace(BASE + 'hjemmel/' + n + '/'); A = Namespace(BASE + 'aktor/'); g.bind('hj', H); g.bind('akt', A)
        lov = URIRef(d['lov_uri']); g.add((lov, RDF.type, ELI.LegalResource)); g.add((lov, ELI.title, Literal(d['lov'], lang='nb')))
        fsk = URIRef(d['forskrift_uri']) if d.get('forskrift_uri') else None
        if fsk: g.add((fsk, RDF.type, ELI.LegalResource)); g.add((fsk, ELI.based_on, lov))
        for a in d['aktorer']: g.add((A[a['id']], RDF.type, DPV.Entity)); g.add((A[a['id']], RDFS.label, Literal(a['navn'], lang='nb')))
        for h in d['hjemler']:
            p = H[h['id']]; best = URIRef(h['lovdata']); erf = '/forskrift/' in h['lovdata']
            g.add((best, RDF.type, ELI.LegalResourceSubdivision)); g.add((best, ELI.is_part_of, fsk if erf and fsk else lov))
            g.add((p, RDF.type, DPV.Process)); g.add((p, RDFS.label, Literal(h['bestemmelse'], lang='nb'))); g.add((p, DPV.hasLegalBasis, best))
            g.add((p, DPV.hasProcessing, DPV[typer[h['type']]]))
            pu = BNode(); g.add((p, DPV.hasPurpose, pu)); g.add((pu, RDF.type, DPV.Purpose)); g.add((pu, DCT.description, Literal(h['formal'], lang='nb')))
            for a in h['avgiver']: g.add((p, DPV.hasDataSource, A[a]))
            for a in h['mottaker']: g.add((p, DPV.hasRecipient, A[a]))
            for o in h['opplysninger']: g.add((p, DPV.hasPersonalData, self.uri(o)))
            for s in h['sakstyper']: g.add((p, DCT.coverage, Literal(s)))
            if h.get('presiserer'): g.add((p, DCT.isPartOf, H[h['presiserer']]))
            if h.get('vilkar'): g.add((p, SKOS.scopeNote, Literal(h['vilkar'], lang='nb')))
            if h.get('merknad'): g.add((p, SKOS.editorialNote, Literal(h['merknad'], lang='nb')))
            g.add((p, SKOS.editorialNote, Literal(f"Juridisk status: {h['status']}", lang='nb')))
        return g

STOTTE = ''.join(f'<{RWS}{k}> a <http://www.w3.org/2004/02/skos/core#Concept> .\n' for k in ('self-composed', 'derived-from-source', 'direct-from-source'))
def shacl(g, former, egne, ont=None, ekstra=()):
    from pyshacl import validate
    d = Graph(); d += g; d.parse(data=STOTTE, format='turtle')
    for e in ekstra: d += e
    ok, rg, _ = validate(d, shacl_graph=Graph().parse(former), ont_graph=Graph().parse(ont) if ont else None, inference='rdfs' if ont else 'none', advanced=True)
    c = collections.Counter()
    for res in rg.subjects(RDF.type, SH.ValidationResult):
        f = str(rg.value(res, SH.focusNode))
        if not any(f.startswith(e) for e in egne): continue  # bare brudd i våre egne data teller
        c[(str(rg.value(res, SH.resultSeverity)).split('#')[-1], str(rg.value(res, SH.resultPath)).split('#')[-1].split('/')[-1], str(rg.value(res, SH.resultMessage))[:100])] += 1
    return c

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--uten-shacl', action='store_true'); ap.add_argument('--ut', default='bygg'); a = ap.parse_args()
    r = Repo(); b = Bygger(r); os.makedirs(a.ut, exist_ok=True); alle_beg = Graph(); feil = 0
    egne = [s['base'] for s in r.samlinger.values()] + [BASE]
    kjente = Graph()  # alle begreper repoet kjenner, slik at relasjoner på tvers av samlinger kan kontrolleres
    for i in list(r.begreper) + list(r.eksterne): kjente.add((b.uri(i), RDF.type, SKOS.Concept))
    for sid in r.samlinger:
        g = b.begreper(sid); alle_beg += g; p = f'{a.ut}/begreper-{sid}.ttl'; g.serialize(p, format='turtle')
        print(p, len(g), 'tripler')
        if not a.uten_shacl:
            c = shacl(g, 'eksterne/shacl/skos-ap-no-begrep.ttl', [r.samlinger[sid]['base']], ekstra=[kjente])
            for k, v in c.items(): print('   ', v, k); feil += v if k[0] == 'Violation' else 0
    for n in r.skjemaer:
        g = b.modell(n); p = f'{a.ut}/informasjonsmodell-{n}.ttl'; g.serialize(p, format='turtle'); print(p, len(g), 'tripler')
        if not a.uten_shacl:
            fg = b.modell('felles') if n != 'felles' else Graph()
            c = shacl(g, 'eksterne/shacl/modelldcat-ap-no.ttl', [BASE + 'modell/' + n, BASE + 'informasjonsmodell/' + n], ont='eksterne/ontologi/modelldcatno.ttl', ekstra=[kjente, fg])
            for k, v in c.items(): print('   ', v, k); feil += v if k[0] == 'Violation' else 0
    for f in r.hjemmelsfiler:
        g = b.hjemler(f); p = f'{a.ut}/hjemler-' + os.path.basename(f).replace('.yaml', '.ttl'); g.serialize(p, format='turtle'); print(p, len(g), 'tripler')
    print('SHACL-brudd i egne data:', feil); sys.exit(1 if feil else 0)
