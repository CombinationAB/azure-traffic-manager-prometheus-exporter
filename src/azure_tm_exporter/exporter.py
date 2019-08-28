from .az import az
import logging
import os, re
from time import sleep, time
logger = logging.getLogger(__name__)
from prometheus_client import start_http_server, Counter, Gauge
from .dns import get_nameservers, poll_dns

dns_check = Counter('azure_traffic_manager_dns_check_count', 'Azure Traffic Manager DNS check counter', ['name', 'subscription', 'target', 'target_colour'])
endpoint_online = Gauge('azure_traffic_endpoint_online', 'Azure Traffic Manager DNS check counter', ['name', 'subscription', 'target', 'target_colour'])
endpoint_last_seen = Gauge('azure_traffic_endpoint_last_seen', 'Azure Traffic Manager DNS check counter', ['name', 'subscription', 'target', 'target_colour'])

def run_exporter(name, az_user, az_secret, az_tenant):
    logger.info("Starting exporter")

    result = az('login', '--service-principal', '-u', az_user, '-p', az_secret, '--tenant', az_tenant)
    if not result:
        raise ValueError(f"Service principal {az_user} has no access to any subscriptions")
    subs = [x.get("id","") for x in result]
    logger.info(f"Logged in to subscriptions {(','.join(subs))}")
    restart_after = int(os.environ.get("RESTART_AFTER_ITERATIONS", "0"))
    
    poll_azure_interval = int(os.environ.get("AZ_POLL_INTERVAL", "10"))
    if poll_azure_interval < 1: poll_azure_interval = 10

    start_http_server(int(os.environ.get("PROMETHEUS_PORT", "9400")))
    color_regex = re.compile(os.environ.get("COLOR_REGEX", ".*(blue|green).+"))

    selected_tm = None
    selected_sub = ""
    for sub in subs:
        tms = az('network', 'traffic-manager', 'profile', 'list', '--subscription', sub)
        for tm in tms:
            if tm.get('dnsConfig', {}).get('relativeName','') == name:
                selected_tm = tm
                selected_sub = sub
        if selected_tm: break
    if not selected_tm:
        raise ValueError(f"Traffic manager {name} not found. Check that user {az_user} has at least read access to it")

    fqdn = selected_tm['dnsConfig']['fqdn']
    ns = get_nameservers(fqdn)
    tm_name = selected_tm['name']
    tm_rg = selected_tm['resourceGroup']
    if not ns:
        logger.warning(f"Did not find nameservers for {fqdn}. Skipping DNS metrics.")
    else:
        logger.info(f"Found nameservers for {fqdn}: {ns}")

    ct = 0
    seen = set()
    while restart_after == 0 or ct < restart_after:
        ct += 1
        logger.debug(f"Checking (iteration {ct})")
        # Check DNS
        color = set()
        hosts = set()
        for host, m in [(x, color_regex.match(x)) for x in poll_dns(fqdn, ns)]:
            if m:
                color.add(m.group(1))
            hosts.add(host)
        colorval = ','.join(sorted(color))
        hostval = ','.join(sorted(hosts))
        dns_check.labels(name, selected_sub, hostval, colorval).inc()
        t = time()
        
        processed = set()
        if ct % poll_azure_interval == 0:
            # Check Azure
            logger.info("Checking Azure")
            tmdata = az('network', 'traffic-manager', 'profile', 'show', '--name', tm_name, '--resource-group', tm_rg, '--subscription', sub)
            for ep in tmdata.get("endpoints",[]):
                online = int(ep.get("endpointMonitorStatus", "") == "Online")
                target = ep["target"]
                c = color_regex.match(target)
                if c:
                    color = c.group(1)
                else:
                    color = ""
                labels = (name, selected_sub, target, color)
                seen.add(labels)
                processed.add(labels)
                endpoint_online.labels(*labels).set(online)
                endpoint_last_seen.labels(*labels).set(t)
            for labels in seen:
                if not labels in processed:
                    endpoint_online.labels(*labels).set(0)
        sleep(1)

