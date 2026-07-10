# -*- coding: utf-8 -*-
import os, glob, json
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.environ.get("RAW_BASE_URL","").rstrip("/")
log=os.path.join(HERE,"posted.log")
posted=set(l.strip() for l in open(log,encoding="utf-8")) if os.path.exists(log) else set()
cp=os.path.join(HERE,"captions.json")
caps=json.load(open(cp,encoding="utf-8")) if os.path.exists(cp) else {}
imgs=sorted(glob.glob(os.path.join(HERE,"post-*.png")))
nxt=next((os.path.basename(i) for i in imgs if os.path.basename(i) not in posted), None)
L=[]
if nxt:
    L+=["## 📋 Next post awaiting your approval","",
        f"![preview]({BASE}/{nxt})","","**Caption:**","","```",caps.get(nxt,""),"```","",
        "Scroll down and **Approve** the *publish* job to post this, or **Reject** to skip it."]
else:
    L+=["## ✅ All posts already published","","Add more images to the repo to keep the autopilot going."]
s=os.environ.get("GITHUB_STEP_SUMMARY")
if s: open(s,"a",encoding="utf-8").write("\n".join(L)+"\n")
print("next:", nxt or "none")
