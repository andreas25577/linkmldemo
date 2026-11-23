"""Demosteg 2: Noen foreslår å registrere politiattest i saker om tap av statsborgerskap.
Kjedekontrollen skal stoppe dette, fordi ingen hjemmel for sakstypen gir anledning til å innhente politiattest."""
p = 'logisk/statsborgerskap-tap.yaml'; s = open(p, encoding='utf-8').read()
merke = '  SakOmTapAvStatsborgerskap:\n'
i = s.index('    attributes:\n', s.index(merke)) + len('    attributes:\n')
felt = '''      politiattest:
        description: Politiattest innhentet i saken
        range: Politiattest
        inlined: true
        exact_mappings:
        - fe:politiattest
        annotations:
          saerlig_kategori: true
'''
open(p, 'w', encoding='utf-8').write(s[:i] + felt + s[i:])
print('La til feltet politiattest i', p)
