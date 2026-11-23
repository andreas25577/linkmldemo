# linkmldemo

Demo av hvordan UDI kan forvalte **begreper**, **logiske informasjonsmodeller** og **hjemler** sammen i GitHub, med LinkML og spesifikasjonene til data.norge.

> **Foreløpig utkast.** Innholdet er utledet av statsborgerloven og statsborgerforskriften, men er ikke faglig eller juridisk godkjent. Begrepseierne er fiktive. Hjemlene er en arbeidshypotese og må vurderes av jurist før de brukes. Hold repoet privat.

Utvalget er sakstypene søknad om statsborgerskap, melding om statsborgerskap og tap av statsborgerskap, med de felles begrepene og modellelementene de bruker.

## Tre lag

```
konseptuelt/
  begreper/<eier>.yaml      Begreper etter SKOS-AP-NO, én fil per begrepseier
  eiere.yaml                Begrepseierne og GitHub-brukeren som godkjenner endringer
  samlinger.yaml            Begrepssamlingene og URI-ene deres
  eksterne-begreper.yaml    Begreper vi bruker fra andre, for eksempel Skatteetaten og SSB
  hjemler/statsborgerloven.yaml   Hvilke opplysninger regelverket gir anledning til å innhente og behandle
logisk/
  felles.yaml               Felles modellelementer
  statsborgerskap*.yaml     Én LinkML-modell per sakstype. Importerer felles.
metaskjema/                 LinkML-skjemaene som begreps- og hjemmelsfilene valideres mot
konfig/kontroll.yaml        Hvilke begreper som er sensitive, og hvem som eier hjemmelslaget
verktoy/                    Kontroller og generatorer
demo/                       Manus, issues og endringene som vises i demoen
```

Lagene er koblet slik:

- Et **felt** i en modell peker på et **begrep** med `exact_mappings`. En klasse gjør det samme.
- En **hjemmel** lister begrepene for opplysningene den gjelder, og hvilke **sakstyper** den gjelder for.
- Hver modell har annotasjonen `sakstype`. Da kan kontrollen se om et sensitivt felt i en modell har en hjemmel for samme sakstype.
- Hvert begrep har en **begrepseier**. CODEOWNERS lages fra `eiere.yaml`, så eieren må godkjenne endringer i sine begreper.

## Kontrollene

Arbeidsflyten **Kontroll** kjører på hver pull request:

| Kontroll | Hva den gjør |
|---|---|
| LinkML-lint og -validering | Skjemaene er gyldige. Begreps- og hjemmelsfilene følger metaskjemaene. |
| Referanser | Alle relasjoner, `exact_mappings`, kodeverdier og opplysninger peker på begreper som finnes. |
| Begrepseiere | Hvert begrep har en eier som finnes, og ligger i eierens fil. CODEOWNERS er i takt med `eiere.yaml`. |
| Kjedekontroll | Et felt er sensitivt når begrepet (eller et overbegrep) står i `konfig/kontroll.yaml`. Da må en hjemmel for samme sakstype gi anledning til å innhente eller behandle opplysningen. Hvis ikke, stopper kontrollen. |
| SHACL | Turtle-filene valideres mot SHACL-formene for SKOS-AP-NO-Begrep og ModellDCAT-AP-NO. |
| Konsekvensanalyse | Sammenligner med main og skriver en kommentar: hva er endret, hva bruker det, og hvilke begrepseiere bør se på det. |

Arbeidsflyten **Publiser** kjører på main og ved release. Den bygger Turtle-filer, LinkML-dokumentasjon og nettstedet på GitHub Pages med begrepskart og «Spør regelverket».

## Kjør lokalt

```bash
pip install -r requirements.txt
python verktoy/kontroll.py                 # kontrollene
python verktoy/konsekvens.py <main> .      # konsekvensanalyse mot en annen utsjekk
python verktoy/rdf.py                      # Turtle til bygg/ og SHACL-validering
python verktoy/side.py                     # nettstedet til side/
python verktoy/codeowners.py               # lag CODEOWNERS på nytt etter endring i eiere.yaml
```

## Spesifikasjoner

| Lag | Spesifikasjon | Fil |
|---|---|---|
| Begreper | SKOS-AP-NO-Begrep | `bygg/begreper-*.ttl` |
| Logiske modeller | ModellDCAT-AP-NO | `bygg/informasjonsmodell-*.ttl` |
| Hjemler | DPV og ELI | `bygg/hjemler-*.ttl` |

SHACL-formene og ModellDCAT-ontologien i `eksterne/` er hentet fra Digitaliseringsdirektoratets repoer for spesifikasjonene.

## Hvordan innholdet ble laget

`verktoy/konverter.py` konverterte mellomformatet fra kartleggingen av regelverket til denne strukturen én gang. Etter det er filene i repoet kilden.
