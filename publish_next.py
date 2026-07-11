# -*- coding: utf-8 -*-
"""Publish the next unposted Mudir media (image or Reel) to Instagram (Instagram Login API).
Stdlib only. Env: IG_USER_ID, IG_ACCESS_TOKEN, RAW_BASE_URL. Queue = q-*.png / q-*.mp4."""
import os, sys, glob, time, json, urllib.parse, urllib.request, urllib.error
GRAPH="https://graph.instagram.com/v21.0"
HERE=os.path.dirname(os.path.abspath(__file__))
UID=os.environ.get("IG_USER_ID","").strip(); TOK=os.environ.get("IG_ACCESS_TOKEN","").strip(); BASE=os.environ.get("RAW_BASE_URL","").rstrip("/")
def die(m): print("ERROR:",m); sys.exit(1)
if not (UID and TOK and BASE): die("Missing IG_USER_ID / IG_ACCESS_TOKEN / RAW_BASE_URL")
def post(path, params):
    req=urllib.request.Request(f"{GRAPH}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e: die(f"POST {path} -> {e.code}: {e.read().decode()}")
def get(path, params):
    url=f"{GRAPH}/{path}?"+urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=90) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e: die(f"GET {path} -> {e.code}: {e.read().decode()}")
caps={}; cp=os.path.join(HERE,"captions.json")
if os.path.exists(cp): caps=json.load(open(cp,encoding="utf-8"))
log=os.path.join(HERE,"posted.log")
posted=set(l.strip() for l in open(log,encoding="utf-8")) if os.path.exists(log) else set()
media=sorted(glob.glob(os.path.join(HERE,"q-*.png"))+glob.glob(os.path.join(HERE,"q-*.mp4")))
for m in media:
    name=os.path.basename(m)
    if name in posted: continue
    url=f"{BASE}/{name}"; caption=caps.get(name,"مدير — مساعدك الذكي لإدارة مشروعك الصغير")
    if name.lower().endswith(".mp4"):
        print("Publishing REEL", name)
        c=post(f"{UID}/media", {"media_type":"REELS","video_url":url,"caption":caption,"access_token":TOK})
        cid=c.get("id") or die(f"no creation id: {c}")
        # poll processing status (reels need time)
        for _ in range(30):
            time.sleep(10)
            st=get(f"{cid}", {"fields":"status_code","access_token":TOK})
            code=st.get("status_code"); print(" status:",code)
            if code=="FINISHED": break
            if code=="ERROR": die(f"reel processing error: {st}")
        pub=post(f"{UID}/media_publish", {"creation_id":cid,"access_token":TOK})
    else:
        print("Publishing IMAGE", name)
        c=post(f"{UID}/media", {"image_url":url,"caption":caption,"access_token":TOK})
        cid=c.get("id") or die(f"no creation id: {c}")
        time.sleep(15)
        pub=post(f"{UID}/media_publish", {"creation_id":cid,"access_token":TOK})
    print("Published:",pub)
    open(log,"a",encoding="utf-8").write(name+"\n")
    print("Recorded",name); sys.exit(0)
print("Queue empty — all posted. Add more q-*.png / q-*.mp4 to continue.")
