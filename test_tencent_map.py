# test_tencent_map.py
import os, socket, requests, time, json, datetime

KEY = os.environ.get("TENCENT_MAP_KEY", "")
HOST = "apis.map.qq.com"

def pretty(msg):
    print(f"[{datetime.datetime.now().isoformat()}] {msg}")

def check_env():
    pretty("ENV check: TENCENT_MAP_KEY present: " + str(bool(KEY)))
    pretty("Proxy envs: HTTP_PROXY=%s HTTPS_PROXY=%s" % (os.environ.get("HTTP_PROXY"), os.environ.get("HTTPS_PROXY")))

def check_dns():
    pretty("== DNS check ==")
    try:
        addrs = socket.getaddrinfo(HOST, 443)
        pretty("getaddrinfo result (first 3): %s" % str(addrs[:3]))
    except Exception as e:
        pretty("DNS/resolution error: %r" % e)

def test_geocoder_address():
    pretty("== Geocoder (address -> coord) test ==")
    url = "https://apis.map.qq.com/ws/geocoder/v1/"
    params = {"address": "昆明理工大学", "key": KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        pretty("Request URL: %s" % r.url.replace(KEY, "***"))
        pretty("HTTP status: %s" % r.status_code)
        txt = r.text
        pretty("Response text (first 1000 chars): %s" % txt[:1000])
        try:
            j = r.json()
            pretty("Parsed JSON keys: %s" % list(j.keys()))
            pretty("Parsed JSON (short): %s" % json.dumps(j, ensure_ascii=False)[:1000])
        except Exception as e:
            pretty("JSON parse error: %r" % e)
    except Exception as e:
        pretty("Exception while requesting geocoder: %r" % e)

def test_reverse(lat="24.854887", lng="102.859035"):
    pretty("== Reverse geocoder (coord -> address) test ==")
    url = "https://apis.map.qq.com/ws/geocoder/v1/"
    params = {"location": f"{lat},{lng}", "key": KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        pretty("Request URL: %s" % r.url.replace(KEY, "***"))
        pretty("HTTP status: %s" % r.status_code)
        pretty("Response text (first 1000 chars): %s" % r.text[:1000])
    except Exception as e:
        pretty("Exception while requesting reverse geocoder: %r" % e)

if __name__ == "__main__":
    check_env()
    check_dns()
    test_geocoder_address()
    test_reverse()
