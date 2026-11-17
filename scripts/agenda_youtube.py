#!/usr/bin/env python3
"""Lista os vídeos programados pela API do YouTube para a agenda da Vox Dei.

Uso:
  python3 scripts/agenda_youtube.py [videoId ...] > /tmp/yt_agenda.json

Sem argumentos: devolve os vídeos do canal que estão PROGRAMADOS (private + publishAt).
Com ids (os que já estão na agenda com youtubeId): devolve também o estado atual deles,
para a agenda marcar "Publicado" quando o horário passar ou detectar remoção.

Saída (JSON, lista): id, titulo, publishAt (UTC), data e hora (Brasília), tipo (Short|Longo),
duracaoSeg, privacidade, estado (agendado|publicado|privado|removido), link, thumb (URL).
Os Shorts do Buffer não entram aqui: o Buffer sobe na hora, nunca como private + publishAt.
Usa YT_CLIENT_ID, YT_CLIENT_SECRET e YT_REFRESH_TOKEN do ambiente. Nunca imprime os valores.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

SP = ZoneInfo("America/Sao_Paulo")
API = "https://www.googleapis.com/youtube/v3/"

d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                            "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
TOK = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", d))["access_token"]


def get(path, **q):
    req = urllib.request.Request(API + path + "?" + urllib.parse.urlencode(q), headers={"Authorization": "Bearer " + TOK})
    return json.load(urllib.request.urlopen(req))


def segundos(iso):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d_, h, mi, s = (int(x or 0) for x in m.groups())
    return d_ * 86400 + h * 3600 + mi * 60 + s


uploads = get("channels", part="contentDetails", mine="true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
ids, token = [], None
for _ in range(2):  # últimos 100 uploads bastam: programados são sempre recentes
    q = {"part": "contentDetails", "maxResults": 50, "playlistId": uploads}
    if token:
        q["pageToken"] = token
    r = get("playlistItems", **q)
    ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
    token = r.get("nextPageToken")
    if not token:
        break

pedidos = [a for a in sys.argv[1:] if a]
alvo = list(dict.fromkeys(pedidos + ids))
achados = {}
for i in range(0, len(alvo), 50):
    for v in get("videos", part="snippet,status,contentDetails", id=",".join(alvo[i:i + 50])).get("items", []):
        achados[v["id"]] = v

agora = dt.datetime.now(dt.timezone.utc)
out = []
for vid in alvo:
    v = achados.get(vid)
    if not v:
        if vid in pedidos:
            out.append({"id": vid, "estado": "removido"})
        continue
    st, sn = v["status"], v["snippet"]
    pub = st.get("publishAt")
    if not pub and vid not in pedidos:
        continue  # só entra o que foi programado pela API (ou já está na agenda)
    quando = pub or sn.get("publishedAt")
    t = dt.datetime.fromisoformat(quando.replace("Z", "+00:00"))
    priv = st.get("privacyStatus")
    if priv == "public" or (pub and t <= agora and priv != "private"):
        estado = "publicado"
    elif pub:
        estado = "agendado"
    else:
        estado = "privado"
    seg = segundos(v["contentDetails"].get("duration"))
    th = sn.get("thumbnails", {})
    thumb = (th.get("maxres") or th.get("standard") or th.get("high") or th.get("medium") or {}).get("url", "")
    loc = t.astimezone(SP)
    out.append({"id": vid, "titulo": sn.get("title", ""), "publishAt": quando, "data": loc.strftime("%Y-%m-%d"),
                "hora": loc.strftime("%H:%M"), "tipo": "Short" if seg <= 180 else "Longo", "duracaoSeg": seg,
                "privacidade": priv, "estado": estado, "link": f"https://youtu.be/{vid}", "thumb": thumb})

json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
print()
