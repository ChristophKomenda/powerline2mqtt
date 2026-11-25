import re
MAC = re.compile(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}')

def parse_topology(text):
    rows = {}
    for line in text.splitlines():
        p = line.split()
        if not p or p[0] not in ('LOC', 'REM'):
            continue
        if len(p) < 7 or not MAC.fullmatch(p[3]) or not MAC.fullmatch(p[4]):
            raise ValueError('Malformed topology row')
        def rate(s):
            if s.lower() in ('n/a', '-', 'unknown'):
                return None
            return int(s)
        mac = p[3].upper()
        rows[mac] = dict(mac=mac, locality=p[0], role=p[1], tei=int(p[2]),
                         bda=p[4].upper(), tx=rate(p[5]), rx=rate(p[6]),
                         chipset=p[7] if len(p)>7 else None,
                         firmware=' '.join(p[8:]) or None)
    if not any(r['locality']=='LOC' for r in rows.values()):
        raise ValueError('No local adapter in topology')
    return rows
