# -*- coding: utf-8 -*-
import os, glob, json
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.environ.get("RAW_BASE_URL","").rstrip("/")
log=os.path.join(HERE,"posted.log"); posted=set(l.strip() for l in open(log,encoding="utf-8")) if os.path.exists(log) else set()
cp=os.path.join(HERE,"captions.json"); caps=json.load(open(cp,encoding="utf-8")) if os.path.exists(cp) else {}
media=sorted(glob.glob(os.path.join(HERE,"q-*.png"))+glob.glob(os.path.join(HERE,"q-*.mp4")))
nxt=next((os.path.basename(m) for m in media if os.path.basename(m) not in posted), None)
L=[]
if nxt:
    kind="🎬 Reel (video)" if nxt.endswith(".mp4") else "🖼️ Image"
    L+=[f"## 📋 Next post awaiting approval — {kind}","",f"**File:** `{nxt}`","",f"[▶️ Open the {'video' if nxt.endswith('.mp4') else 'image'} to preview]({BASE}/{nxt})","","**Caption:**","","```",caps.get(nxt,""),"```","","Approve the *publish* job below to post it, or Reject to skip."]
else:
    L+=["## ✅ Queue empty — all posted","","Add more q-*.png / q-*.mp4 to keep going."]
s=os.environ.get("GITHUB_STEP_SUMMARY")
if s: open(s,"a",encoding="utf-8").write("\n".join(L)+"\n")
print("next:", nxt or "none")
