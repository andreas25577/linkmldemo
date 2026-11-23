#!/usr/bin/env bash
# Lager én gren per demosteg fra main og dytter dem til GitHub.
# Kjør fra roten av repoet etter at main er dyttet: bash demo/lag-grener.sh
set -euo pipefail
git checkout main
lag() {  # gren, skript, melding
  git checkout -B "$1" main
  python "demo/$2"
  git add -A && git commit -m "$3"
  git push -u origin "$1" --force
  git checkout main
}
lag demo/steg1-forskriftsendring steg1_forskriftsendring.py "Tenkt endring: HK-dir i stedet for Kompetanse Norge i stbf § 14-8"
lag demo/steg2-sensitivt-felt   steg2_sensitivt_felt.py   "Legg til politiattest i sak om tap av statsborgerskap"
lag demo/steg3-begrepsendring   steg3_begrepsendring.py   "Presiser definisjonen av straffereaksjon"
echo "Grenene er dyttet. Åpne en pull request for hver av dem mot main."
