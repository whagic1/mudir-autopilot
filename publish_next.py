# -*- coding: utf-8 -*-
"""Publish the next unposted Mudir image to Instagram (Instagram Login API).
Stdlib only. Env: IG_USER_ID, IG_ACCESS_TOKEN, RAW_BASE_URL."""
import os, sys, glob, time, json, urllib.parse, urllib.request, urllib.error

GRAPH = "https://graph.instagram.com/v21.0"
HERE  = os.path.dirname(os.path.abspath(__file__))
UID   = os.environ.get("IG_USER_ID","").strip()
TOK   = os.environ.get("IG_ACCESS_TOKEN","").strip()
BASE  = os.environ.get("RAW_BASE_URL","").rstrip("/")

def die(m): print("ERROR:",m); sys.exit(1)
if not (UID and TOK and BASE): die("Missing IG_USER_ID / IG_ACCESS_TOKEN / RAW_BASE_URL")

def api(path, params):
    data=urllib.parse.urlencode(params).encode()
    req=urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e: die(f"Graph API {e.code}: {e.read().decode()}")

caps={}
cp=os.path.join(HERE,"captions.json")
if os.path.exists(cp): caps=json.load(open(cp,encoding="utf-8"))

log=os.path.join(HERE,"posted.log")
posted=set(l.strip() for l in open(log,encoding="utf-8")) if os.path.exists(log) else set()

imgs=sorted(glob.glob(os.path.join(HERE,"post-*.png")))
for img in imgs:
    name=os.path.basename(img)
    if name in posted: continue
    image_url=f"{BASE}/{name}"
    caption=caps.get(name,"مدير — مساعدك الذكي لإدارة مشروعك الصغير")
    print("Publishing", name, "->", image_url)
    c=api(f"{UID}/media", {"image_url":image_url,"caption":caption,"access_token":TOK})
    cid=c.get("id") or die(f"no creation id: {c}")
    time.sleep(15)
    p=api(f"{UID}/media_publish", {"creation_id":cid,"access_token":TOK})
    print("Published:",p)
    open(log,"a",encoding="utf-8").write(name+"\n")
    print("Recorded",name); sys.exit(0)
print("All posts already published. Add more images to posts/ to continue.")
