# -*- coding: utf-8 -*-
"""Publish the next unposted Mudir media (image or Reel) to Instagram (Instagram Login API).
Stdlib only. Env: IG_USER_ID, IG_ACCESS_TOKEN, RAW_BASE_URL. Queue = q-*.png / q-*.mp4.
Resilient to transient Meta errors: retries 5xx/"Internal server error" a few times, uses short
timeouts, and if a Reel is still processing it exits cleanly so the SAME item retries next run
(no wasted/failed day). Reels get a readable cover via thumb_offset. .mp4 supersedes same-name .png."""
import os, sys, glob, time, json, urllib.parse, urllib.request, urllib.error
GRAPH="https://graph.instagram.com/v21.0"
HERE=os.path.dirname(os.path.abspath(__file__))
UID=os.environ.get("IG_USER_ID","").strip(); TOK=os.environ.get("IG_ACCESS_TOKEN","").strip(); BASE=os.environ.get("RAW_BASE_URL","").rstrip("/")
THUMB_MS="700"
def die(m,code=1): print(("ERROR: " if code else "")+m); sys.exit(code)
if not (UID and TOK and BASE): die("Missing IG_USER_ID / IG_ACCESS_TOKEN / RAW_BASE_URL")

def api(path, params, method="POST", tries=4):
    """Call the Graph API with retry on transient (5xx / Meta internal) errors."""
    for i in range(tries):
        try:
            if method=="POST":
                req=urllib.request.Request(f"{GRAPH}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
            else:
                req=urllib.request.Request(f"{GRAPH}/{path}?"+urllib.parse.urlencode(params), method="GET")
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body=e.read().decode()
            transient = e.code>=500 or "Internal server error" in body or '"code":2' in body or '"is_transient":true' in body
            if transient and i<tries-1:
                print(f"  transient error {e.code}, retry {i+1}/{tries-1} in 20s"); time.sleep(20); continue
            die(f"{method} {path} -> {e.code}: {body}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if i<tries-1:
                print(f"  network error, retry {i+1}/{tries-1} in 20s: {e}"); time.sleep(20); continue
            die(f"{method} {path} network error: {e}")

caps={}; cp=os.path.join(HERE,"captions.json")
if os.path.exists(cp): caps=json.load(open(cp,encoding="utf-8"))
log=os.path.join(HERE,"posted.log")
posted=set(l.strip() for l in open(log,encoding="utf-8")) if os.path.exists(log) else set()
raw=glob.glob(os.path.join(HERE,"q-*.png"))+glob.glob(os.path.join(HERE,"q-*.mp4"))
by={}
for m in raw:
    b=os.path.splitext(os.path.basename(m))[0]
    if b not in by or m.lower().endswith(".mp4"): by[b]=m
media=sorted(by.values(), key=lambda p: os.path.basename(p))
for m in media:
    name=os.path.basename(m); base=os.path.splitext(name)[0]
    if name in posted: continue
    if name.lower().endswith(".mp4") and (base+".png") in posted: continue
    url=f"{BASE}/{name}"; caption=caps.get(name,"مدير — مساعدك الذكي لإدارة مشروعك الصغير")
    if name.lower().endswith(".mp4"):
        print("Publishing REEL", name)
        c=api(f"{UID}/media", {"media_type":"REELS","video_url":url,"caption":caption,
                                "thumb_offset":THUMB_MS,"share_to_feed":"true","access_token":TOK})
        cid=c.get("id") or die(f"no creation id: {c}")
        finished=False
        for _ in range(24):  # ~4 min max
            time.sleep(10)
            st=api(f"{cid}", {"fields":"status_code","access_token":TOK}, method="GET")
            code=st.get("status_code"); print(" status:",code)
            if code=="FINISHED": finished=True; break
            if code=="ERROR": die(f"reel processing error: {st}")
        if not finished:
            # Instagram still processing — don't force-publish; exit cleanly so this SAME item retries next run
            die("Reel still processing after 4 min (Instagram slow); will retry next run.", code=0)
        pub=api(f"{UID}/media_publish", {"creation_id":cid,"access_token":TOK})
    else:
        print("Publishing IMAGE", name)
        c=api(f"{UID}/media", {"image_url":url,"caption":caption,"access_token":TOK})
        cid=c.get("id") or die(f"no creation id: {c}")
        time.sleep(15)
        pub=api(f"{UID}/media_publish", {"creation_id":cid,"access_token":TOK})
    print("Published:",pub)
    open(log,"a",encoding="utf-8").write(name+"\n")
    print("Recorded",name); sys.exit(0)
print("Queue empty — all posted. Add more q-*.png / q-*.mp4 to continue.")
