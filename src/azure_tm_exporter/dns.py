import dns.name, dns.resolver

def poll_dns(rec, ns):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = list(map(str, ns))
    try:
        r = list(resolver.query(rec, 'CNAME', raise_on_no_answer=False))
    except dns.resolver.NXDOMAIN:
        pass
    if not r:
        r = list(resolver.query(rec, 'A', raise_on_no_answer=False))
    return list(map(str, r))

def get_nameservers(rec):
    resolver = dns.resolver.Resolver(configure=False)
    rec = dns.name.from_text(str(rec))
    recs = set()
    while True:
        if recs: break # Stop as soon as we have nameservers
        try:
            for r in dns.resolver.query(rec, 'NS', raise_on_no_answer=False):
                try:
                    for raddr in dns.resolver.query(r.target, 'A', raise_on_no_answer=False):
                        recs.add(str(raddr.address))
                except dns.resolver.NXDOMAIN:
                    pass
        except dns.resolver.NXDOMAIN:
            # No NS records, try parent
            pass
        if len(rec.labels) <= 3: # no more parents to try
            break
        rec = rec.parent()

    return recs