#!/usr/bin/env python3
"""Sobe um Short da Vox Dei direto no YouTube (API), já programado (private + publishAt).

Uso:
  python3 scripts/upload_short_youtube.py <video.mp4> <publishAt-UTC> <titulo> <descricao> <tag1,tag2,...>
Categoria 22, pt-BR (idioma e áudio), madeForKids false, containsSyntheticMedia false (regra dos Shorts).
Usa YT_CLIENT_ID, YT_CLIENT_SECRET e YT_REFRESH_TOKEN do ambiente. Nunca imprime os valores.
"""
import json, os, sys, urllib.parse, urllib.request

if len(sys.argv) != 6:
    raise SystemExit(__doc__)
vid, publish_at, title, desc, tags = sys.argv[1:]
d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                            "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", d))["access_token"]
assert len(title) <= 100, "título > 100"
body = {"snippet": {"title": title, "description": desc, "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "categoryId": "22", "defaultLanguage": "pt-BR", "defaultAudioLanguage": "pt-BR"},
        "status": {"privacyStatus": "private", "publishAt": publish_at, "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": False}}
size = os.path.getsize(vid)
req = urllib.request.Request(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    data=json.dumps(body).encode(),
    headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json; charset=UTF-8",
             "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}, method="POST")
loc = urllib.request.urlopen(req).headers["Location"]
with open(vid, "rb") as f:
    req = urllib.request.Request(loc, data=f.read(), headers={"Authorization": "Bearer " + tok, "Content-Type": "video/mp4"}, method="PUT")
r = json.load(urllib.request.urlopen(req, timeout=900))
print("id", r["id"], json.dumps(r.get("status")))
