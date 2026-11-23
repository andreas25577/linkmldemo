# Manus for demoen (20 minutter)

Repoet viser hvordan begreper, logiske modeller og hjemler kan forvaltes sammen i GitHub med LinkML.
Innholdet er et foreløpig utkast for statsborgerskap. **Begrepseierne er fiktive, og ingen begreper eller hjemler er godkjent.**

Forberedelse: dytt main, kjør `bash demo/lag-grener.sh`, opprett issuene i `demo/issues.md`, og åpne en pull request per gren.
Vent til arbeidsflyten «Kontroll» er ferdig på alle tre.

## 0. Utgangspunktet (2 min)
Vis mappestrukturen i README. Poenget: tre lag i samme repo.
- `konseptuelt/begreper/` er delt opp per begrepseier. Hver fil har én eier.
- `logisk/` er LinkML-skjemaer. Hvert felt peker på et begrep med `exact_mappings`.
- `konseptuelt/hjemler/` sier hvilke opplysninger regelverket gir anledning til å innhente, og for hvilke sakstyper.
Åpne `.github/CODEOWNERS` og vis at den er generert fra `konseptuelt/eiere.yaml`.

## 1. En regelverksendring (5 min)
Issue 1 og pull requesten fra `demo/steg1-forskriftsendring`.
- Vis diffen: én linje i hjemmelsfilen.
- Vis kommentaren fra Kontroll. Konsekvensanalysen viser hvilke begreper hjemmelen gjelder, hvilke felt i modellene som bygger på den, og hvilke begrepseiere som bør se på den.
- Poeng: Vi vet hva en lovendring berører før den er gjennomført i systemene.

## 2. Et sensitivt felt uten hjemmel (5 min)
Issue 2 og pull requesten fra `demo/steg2-sensitivt-felt`.
- Diffen legger til feltet `politiattest` i sak om tap av statsborgerskap.
- Kontrollen er rød. Kjedekontrollen finner ingen hjemmel for sakstypen «statsborgerskap-tap» som gir anledning til å innhente politiattest.
- Vis tabellen over sensitive felt. De andre politiattest-feltene er dekket av § 7 fjerde ledd og § 20 annet ledd.
- Poeng: Personvern og hjemmel blir en del av modelleringen, ikke noe som sjekkes etterpå. Hva som er riktig hjemmel, avgjør en jurist. Kontrollen sier bare at koblingen mangler.

## 3. En begrepsendring som berører andre (4 min)
Issue 3 og pull requesten fra `demo/steg3-begrepsendring`.
- Diffen endrer definisjonen av straffereaksjon i filen til Fagenhet for vandel og sikkerhet.
- CODEOWNERS ber eieren om godkjenning.
- Konsekvensanalysen viser at begrepet også brukes av Fagenhet for statsborgerskap og Fagenhet for tap og tilbakekall, av modellene for alle tre sakstypene og av fire hjemler.
- Poeng: Begrepseierne blir synlige, og de som bruker et begrep, får vite om endringer.

## 4. Publisering (2 min)
Flett steg 3, og lag en release `v0.1.0`.
- Arbeidsflyten «Publiser» bygger Turtle-filer etter SKOS-AP-NO, ModellDCAT-AP-NO og DPV, validerer dem mot SHACL-formene til Digdir, og legger dem ved releasen.
- Pages oppdateres med begrepskartet og modelldokumentasjonen.

## 5. Spør regelverket (2 min)
Åpne Pages, fanen «Spør regelverket».
- «Hva kan UDI innhente i en sakstype?» for søknad om statsborgerskap.
- «Hvem må involveres hvis vi endrer et begrep?» for straffereaksjon.
- I begrepskartet: slå av og på eiere, og huk av «Vis bare relasjoner på tvers av eiere».

## Spørsmål som ofte kommer
- *Hvem skal skrive YAML?* Fagfolk kan bruke issues. Informasjonsforvaltning gjør endringen. Senere kan et skjema eller en enkel editor lage pull requesten.
- *Hva med data.norge?* Turtle-filene kan høstes fra en fast adresse på Pages eller fra releasen.
- *Hvorfor LinkML?* Ett skjemaspråk for modellene, og generatorer for JSON Schema, SHACL, dokumentasjon og ER-diagram.
