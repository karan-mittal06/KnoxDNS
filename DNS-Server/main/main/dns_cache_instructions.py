import datetime
import socket
import time
import threading
import requests
from dnslib import DNSRecord,QTYPE
from main import UPSTREAM_DNS, UPSTREAM_PORT
import json
import os

CACHE_FILE = "dns_cache.json"
url = "http://127.0.0.1:8000/predict"
DEST_PATH = "/Users/deathknight1/knoxdns_clone/KnoxDNS/Website/Frontend/src/cache.json"

if os.path.exists(CACHE_FILE) and os.stat(CACHE_FILE).st_size > 0:
    with open(CACHE_FILE) as file:
        try:
            flaggingActivity = json.load(file)
            daily = flaggingActivity.get("daily", {})
            flaggedSites = flaggingActivity.get("flaggedSites", {})
        except json.JSONDecodeError:
            flaggingActivity = {"flaggedSites": {}, "daily": {}}
            daily = flaggingActivity["daily"]
            flaggedSites = flaggingActivity["flaggedSites"]
else:
    flaggingActivity = {"flaggedSites": {}, "daily": {}}
    daily = flaggingActivity["daily"]
    flaggedSites = flaggingActivity["flaggedSites"]


flaggedSites = flaggingActivity.get("flaggedSites", {})
daily = flaggingActivity.get("daily", {})

def save_cache():
    """saves the data back to the json"""
    flaggingActivity = {
        "daily" : daily,
        "flaggedSites" : flaggedSites
    }
    with open(CACHE_FILE, 'w') as k:
        json.dump(flaggingActivity, k, indent= 4)


def refresh_domain(domain):
    """make a targeted refresh for a domain due to ttl running out and hasn't yet been updated"""
    try:
        query = DNSRecord.question(domain, QTYPE.A)
        data = query.pack()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as upstream_socket:
            upstream_socket.settimeout(2)
            upstream_socket.sendto(data, (UPSTREAM_DNS, UPSTREAM_PORT))
            response, _ = upstream_socket.recvfrom(512)

            refresh_response = DNSRecord.parse(response)

            for rr in refresh_response.rr:
                if rr.rtype == 1:
                    ip = str(rr.rdata)
                    ttl = int(rr.ttl)
                    break
                elif rr.rtype == 28:
                    ip = str(rr.rdata)
                    ttl = int(rr.ttl)
                    break

            if ip and ttl:
                now = time.time()
                entry = flaggedSites[domain]
                date = datetime.datetime.now().strftime('%m-%d')

                flaggedSites[domain].update({
                    "ip": str(ip),
                    "ttl": int(str(ttl)),
                    "timestamp": int(now),
                    "next_refresh": int(now + ttl),
                    "malicious": bool(entry.get("malicious")),
                    "flagged": int(entry.get("flagged")),
                    "type" : entry.get("type")
                })

                daily[date].update({
                    "goodCount" : daily[date].get("goodCount"),
                    "badCount" : daily[date].get("badCount")
                    })

                save_cache()
                print(f"[REFRESH] {domain} -> {ip}, TTL : {ttl}")
            else:
                print(f"[WARNING] no valid response for {domain}")

    except socket.timeout:
        print("refresh failed to connect")
    except Exception as e:
        print("Refresh Error:", e)

def get_ip(domain):
    """Check cache and return IP if valid; otherwise, None."""
    if domain in flaggedSites:
        entry = flaggedSites[domain]
        date = datetime.datetime.now().strftime('%m-%d')
        today = daily[date]
        if time.time() < entry["next_refresh"]:
            entry["flagged"] += 1
            today["badCount"] = today["badCount"] + 1 if entry["malicious"] else today["badCount"]
            today["goodCount"] = today["goodCount"] + 1 if not entry["malicious"] else today["goodCount"]

            save_cache()
            return entry
        else:
            refresh_domain(domain)
            return flaggedSites[domain]
    else:
        return 0        # if the domain not in cache it will return 0 to indicate a new domain has been encountered

def insert(domain, record):
    """Insert a new domain into cache with TTL handling."""
    malicious = determine_malicious(domain)
    print(f"for {domain} determined : {malicious}")

    if malicious == 1:
        malicious = True
        kind = "bad"
    else:
        malicious = False
        kind = "good"

    ip = "142.251.42.78"    # change to warning page
    ttl = 60
    for rr in record.rr:
        if rr.rtype == 1:
            ip = str(rr.rdata)
            ttl = int(rr.ttl)
        elif rr.rtype == 28:
            ip = str(rr.rdata)
            ttl = int(rr.ttl)

    now = time.time()
    date = datetime.datetime.now().strftime('%m-%d')
    flags = 1

    badCount = daily.get(date, {}).get("badCount", 0)
    goodCount = daily.get(date, {}).get("goodCount", 0)

    flaggedSites[domain] = {
        "ip": str(ip),
        "ttl": int(ttl),
        "timestamp": int(now),
        "next_refresh": int(now + ttl),
        "malicious": bool(malicious),
        "flagged" : int(flags),
        "type" : kind
    }

    daily[date] = {
        "badCount" : badCount + 1 if malicious else badCount,
        "goodCount" : goodCount + 1 if not malicious else goodCount
    }
    save_cache()


def refresh_cache():
    """Periodically refresh expired cache entries."""
    while True:
        now = time.time()
        for domain in list(flaggedSites.keys()):
            entry = flaggedSites.get(domain, {})
            if now >= int(entry.get("next_refresh", 0)):
                try:
                    query = DNSRecord.question(domain, QTYPE.A)
                    data = query.pack()
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as upstream_socket:
                        upstream_socket.settimeout(2)
                        upstream_socket.sendto(data, (UPSTREAM_DNS, UPSTREAM_PORT))
                        response, _ = upstream_socket.recvfrom(512)

                        refresh_response = DNSRecord.parse(response)

                        for rr in refresh_response.rr:
                            if rr.rtype == 1:
                                ip = str(rr.rdata)
                                ttl = int(rr.ttl)
                                break
                            elif rr.rtype == 28:
                                ip = str(rr.rdata)
                                ttl = int(rr.ttl)
                                break

                        if ip and ttl:
                            now = time.time()
                            date = datetime.datetime.now().strftime('%m-%d')
                            entry = flaggedSites[domain]

                            flaggedSites[domain].update({
                                "ip" : str(ip),
                                "ttl" : int(str(ttl)),
                                "timestamp" : int(now),
                                "next_refresh" : int(now + ttl),
                                "malicious" : bool(entry.get("malicious", False)),
                                "flagged" : int(entry.get("flagged", 1)),
                                "type": entry.get("type")
                            })

                            daily[date].update({
                                "badCount" : daily[date].get(badCount),
                                "goodCount" : daily[date].get(goodCount)
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

def determine_malicious(domain):
    """send to ai to determinae the nature of the domain"""
    try:
        data = {"url": domain}
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        return response.json().get("predicted_label")
    except requests.RequestException as e:
        print(f"Error communicating with AI classifier: {e}")
        return "Error"


def send_to_backend():
    while True:
        try:
            time.sleep(10)

            daily_data = []
            for i in range(7):
                past_day = datetime.datetime.now() - datetime.timedelta(days=(6 - i))
                date_str = past_day.strftime('%m-%d')

                daily_entry = daily.get(date_str, {})
                daily_data.append({
                    "date": date_str.replace("-", "/"),
                    "badCount": daily_entry.get("badCount", 0),
                    "goodCount": daily_entry.get("goodCount", 0)
                })

            flagged_sites = [
                {
                    "website_name": domain,
                    "type": "bad" if details.get("malicious") else "good",
                    "flagged_count": details.get("flagged", 0)
                }
                for domain, details in flaggedSites.items()
            ]

            output_data = {
                "flaggingActivity": {
                    "daily": daily_data
                },
                "flaggedSites": flagged_sites
            }

            with open(DEST_PATH, 'w') as update_file:
                json.dump(output_data, update_file, indent=2)
                print(f"[SYNC] Backend updated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"[ERROR] send_to_backend(): {e}")


refresh_thread = threading.Thread(target=refresh_cache, daemon=True)
cache_to_domain = threading.Thread(target=send_to_backend, daemon=True)
refresh_thread.start()
cache_to_domain.start()