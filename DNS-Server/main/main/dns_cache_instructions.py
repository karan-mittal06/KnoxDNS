import socket
import time
import threading
from json import JSONDecodeError

from dnslib import DNSRecord, DNSHeader, QTYPE
from main import UPSTREAM_DNS, UPSTREAM_PORT
import json
import os

CACHE_FILE = "dns_cache.json"

if os.path.exists(CACHE_FILE) and os.stat(CACHE_FILE).st_size > 0:          # opened a json file and reading it unless error or empty in which case initializing it as empty
    with open(CACHE_FILE) as file:
        try:
            cached_domains = json.load(file)
        except JSONDecodeError:
            cached_domains = {}
else:
    cached_domains = {}

def save_cache():
    """saves the data back to the json"""
    with open(CACHE_FILE, 'w') as file:
        json.dump(cached_domains, file, indent= 4)


def get_ip(domain):
    """Check cache and return IP if valid; otherwise, None."""
    if domain in cached_domains:
        entry = cached_domains[domain]
        if time.time() < entry["next_refresh"]:
            entry["flagged"] += 1
            save_cache()
            return entry
        else:
            pass    # use threading to pass a targeted refresh and then pass through the entry
    else:
        return 0        # if the domain not in cache it will return 0 to indicate a new domain has been encountered

def insert(domain, record):
    """Insert a new domain into cache with TTL handling."""
    # pass through the ai and the domain name
    malicious = False    # placeholder needs to be changed ******
    ip = "142.251.42.78"
    ttl = 60
    for rr in record.rr:
        if rr.rtype == 1:  # IPv4
            ip = str(rr.rdata)
            ttl = rr.ttl
        elif rr.rtype == 28:  # IPv6
            ip = str(rr.rdata)
            ttl = rr.ttl

    now = time.time()
    flags = 1
    cached_domains[domain] = {
        "ip": str(ip),
        "ttl": int(ttl),
        "timestamp": int(now),
        "next_refresh": int(now + ttl),
        "malicious": bool(malicious),
        "flagged" : int(flags)
    }
    save_cache()


def refresh_cache():
    """Periodically refresh expired cache entries."""
    while True:
        now = time.time()
        for domain in list(cached_domains.keys()):
            entry = cached_domains.get(domain, {})
            if now >= entry.get("next_refresh", 0):
                try:
                    query = DNSRecord.question(domain, QTYPE.A)
                    data = query.pack()
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as upstream_socket:
                        upstream_socket.settimeout(2)
                        upstream_socket.sendto(data, (UPSTREAM_DNS, UPSTREAM_PORT))
                        response, _ = upstream_socket.recvfrom(512)

                        refresh_response = DNSRecord.parse(response)

                        ip = None
                        ttl = None

                        for rr in refresh_response.rr:
                            if rr.rtype == 1:
                                ip = str(rr.rdata)
                                ttl = rr.ttl
                            elif rr.rtype == 28:
                                ip = str(rr.rdata)
                                ttl = rr.ttl

                        if ip and ttl:
                            now = time.time()
                            cached_domains[domain].update({
                                "ip" : str(ip),
                                "ttl" : int(ttl),
                                "timestamp" : int(now),
                                "next_refresh" : int(now + ttl),
                                "malicious" : bool(entry.get("malicious", False)),
                                "flagged" : int(entry.get("flagged"))
                            })
                            save_cache()
                            print(f"[REFRESH] {domain} -> {ip}, TTL : {ttl}")
                        else:
                            print(f"[WARNING] no valid response for {domain}")

                except socket.timeout:
                    print("refresh failed to connect")
                except Exception as e:
                    print("Refresh Error:", e)


        time.sleep(2)                                                                      # refresh time here


def send_to_backend():
    while True:
        time.sleep(10)

refresh_thread = threading.Thread(target=refresh_cache, daemon=True)
refresh_thread.start()