#!/usr/bin/env python3
"""Sobe um vídeo longo da Vox Dei direto no YouTube (API), já programado.

Uso:
  python3 scripts/upload_longo_youtube.py <pasta> <publishAt-UTC> <video.mp4> <thumb.png>
  ex.: python3 scripts/upload_longo_youtube.py /mnt/project-files/longos/2026-11-11-terco-misericordia \
         2026-11-11T17:50:00Z terco-misericordia-2026-11-11.mp4 thumb-terco-2026-11-11.png

<pasta>/youtube-titulo-descricao.txt precisa ter as seções:
  TÍTULO\n<título>\n ... DESCRIÇÃO\n<texto>\nTAGS ... "Tags" do YouTube Studio)\n<tag1, tag2, ...>
Sobe como private + publishAt (vira público na hora marcada), pt-BR, categoria 22,
containsSyntheticMedia true, e define a thumbnail. Usa YT_CLIENT_ID, YT_CLIENT_SECRET e
YT_REFRESH_TOKEN do ambiente (escopo youtube.force-ssl). Nunca imprime os valores.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

if len(sys.argv) != 5:
    raise SystemExit(__doc__)
D, publish_at, video, thumb = sys.argv[1:]
D = D.rstrip("/") + "/"

d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                            "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", d))["access_token"]

txt = open(D + "youtube-titulo-descricao.txt", encoding="utf-8").read()
title = txt.split("TÍTULO\n")[1].split("\n")[0].strip()
desc = txt.split("DESCRIÇÃO\n")[1].split("\nTAGS")[0].strip()
tags = [t.strip() for t in txt.split('"Tags" do YouTube Studio)\n')[1].split("\n")[0].split(",")]
body = {"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "22",
                    "defaultLanguage": "pt-BR", "defaultAudioLanguage": "pt-BR"},
        "status": {"privacyStatus": "private", "publishAt": publish_at, "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": True}}

vid = D + video
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
vid_id = r["id"]
print("id", vid_id, json.dumps(r.get("status")))

ctype = "image/png" if thumb.lower().endswith(".png") else "image/jpeg"
try:
    with open(D + thumb, "rb") as f:
        req = urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid_id}",
                                     data=f.read(), headers={"Authorization": "Bearer " + tok, "Content-Type": ctype}, method="POST")
    print("thumb ok", urllib.request.urlopen(req).status)
except urllib.error.HTTPError as e:
    print("thumb erro", e.code, e.read()[:300])
