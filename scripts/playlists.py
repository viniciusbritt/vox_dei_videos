#!/usr/bin/env python3
"""Playlists do canal Vox Dei (YouTube Data API v3, OAuth).

Uso:
  python3 scripts/playlists.py listar > canal.json
      Lista todos os vídeos do canal (id, título, data, duração) e as
      playlists existentes com seus vídeos.

  python3 scripts/playlists.py aplicar playlists/plano.json
      Cria as playlists que faltam e adiciona os vídeos que ainda não estão
      nelas. Formato:
      [{"titulo": "...", "descricao": "...", "privacidade": "public",
        "videos": ["videoId", ...]}]
      Nunca remove nada. Custo: 50 unidades por playlist criada e por vídeo
      adicionado (cota grátis = 10.000 por dia).

Usa as mesmas variáveis YT_* do scripts/comentarios.py.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comentarios import CANAL_PADRAO, chamar, token  # noqa: E402


def paginar(tok, caminho, params):
    itens, pagina = [], None
    while True:
        p = dict(params, maxResults=50)
        if pagina:
            p["pageToken"] = pagina
        res = chamar(tok, "GET", caminho, p)
        itens += res.get("items", [])
        pagina = res.get("nextPageToken")
        if not pagina:
            return itens


def segundos(iso):
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def playlists_existentes(tok):
    saida = {}
    for pl in paginar(tok, "playlists", {"part": "snippet", "mine": "true"}):
        vids = [i["contentDetails"]["videoId"] for i in
                paginar(tok, "playlistItems", {"part": "contentDetails", "playlistId": pl["id"]})]
        saida[pl["snippet"]["title"]] = {"id": pl["id"], "videos": vids}
    return saida


def listar():
    tok = token()
    canal = os.environ.get("YT_CHANNEL_ID", CANAL_PADRAO)
    ch = chamar(tok, "GET", "channels", {"part": "contentDetails", "id": canal})
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in
           paginar(tok, "playlistItems", {"part": "contentDetails", "playlistId": uploads})]
    videos = []
    for i in range(0, len(ids), 50):
        res = chamar(tok, "GET", "videos", {"part": "snippet,contentDetails,statistics,status",
                                            "id": ",".join(ids[i:i + 50])})
        for v in res.get("items", []):
            videos.append({"id": v["id"], "titulo": v["snippet"]["title"],
                           "data": v["snippet"]["publishedAt"],
                           "segundos": segundos(v["contentDetails"].get("duration")),
                           "views": int(v["statistics"].get("viewCount", 0)),
                           "status": v["status"].get("privacyStatus")})
    json.dump({"videos": videos, "playlists": playlists_existentes(tok)},
              sys.stdout, ensure_ascii=False, indent=2)
    print()


def adicionar(tok, pid, vid):
    # Logo depois de criar a playlist a API às vezes devolve 409; espera e tenta de novo.
    corpo = {"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}
    for tentativa in range(5):
        try:
            return chamar(tok, "POST", "playlistItems", {"part": "snippet"}, corpo)
        except SystemExit as e:
            if "409" not in str(e) or tentativa == 4:
                raise
            time.sleep(3 * (tentativa + 1))


def aplicar(arquivo):
    tok = token()
    with open(arquivo, encoding="utf-8") as f:
        plano = json.load(f)
    existentes = playlists_existentes(tok)
    for pl in plano:
        atual = existentes.get(pl["titulo"])
        if atual:
            pid, ja = atual["id"], set(atual["videos"])
            print(f"playlist já existe: {pl['titulo']}")
        else:
            res = chamar(tok, "POST", "playlists", {"part": "snippet,status"}, {
                "snippet": {"title": pl["titulo"], "description": pl.get("descricao", ""),
                            "defaultLanguage": "pt-BR"},
                "status": {"privacyStatus": pl.get("privacidade", "public")}})
            pid, ja = res["id"], set()
            print(f"playlist criada: {pl['titulo']} -> {pid}")
        for vid in pl["videos"]:
            if vid in ja:
                continue
            adicionar(tok, pid, vid)
            ja.add(vid)
            print(f"  + {vid}")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "listar":
        listar()
    elif len(sys.argv) == 3 and sys.argv[1] == "aplicar":
        aplicar(sys.argv[2])
    else:
        sys.exit(__doc__)
