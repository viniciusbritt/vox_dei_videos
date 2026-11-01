#!/usr/bin/env python3
"""Comentários do YouTube da Vox Dei (YouTube Data API v3, OAuth).

Uso:
  python3 scripts/comentarios.py pendentes [--dias 7] > pendentes.json
      Lista os comentários principais dos últimos N dias que o canal ainda
      não respondeu (custo: 1 unidade de cota por página de 100).

  python3 scripts/comentarios.py responder respostas.json
      Publica as respostas. Formato: [{"commentId": "...", "texto": "..."}]
      (custo: 50 unidades por resposta; cota grátis = 10.000 por dia).
      Antes de publicar, confere de novo se o canal já respondeu, para não
      duplicar.

Variáveis de ambiente (ficam no ambiente da nuvem, nunca no repositório):
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
  YT_CHANNEL_ID (opcional, padrão: canal Vox Dei)
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3"
CANAL_PADRAO = "UCmW-giYuj-VspTkyRwZWwPA"  # @voxdeijesus


def token():
    faltando = [v for v in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(v)]
    if faltando:
        sys.exit("Faltam as variáveis de ambiente: " + ", ".join(faltando))
    dados = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", dados) as r:
        return json.load(r)["access_token"]


def chamar(tok, metodo, caminho, params=None, corpo=None):
    url = f"{API}/{caminho}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=metodo, headers={"Authorization": f"Bearer {tok}"})
    data = None
    if corpo is not None:
        data = json.dumps(corpo).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Erro da API ({e.code}): {e.read().decode()[:500]}")


def respondido_pelo_canal(thread, canal):
    for rep in thread.get("replies", {}).get("comments", []):
        if rep["snippet"].get("authorChannelId", {}).get("value") == canal:
            return True
    return False


def pendentes(dias):
    tok = token()
    canal = os.environ.get("YT_CHANNEL_ID", CANAL_PADRAO)
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=dias)
    saida, pagina = [], None
    while True:
        params = {"part": "snippet,replies", "allThreadsRelatedToChannelId": canal,
                  "order": "time", "maxResults": 100, "textFormat": "plainText"}
        if pagina:
            params["pageToken"] = pagina
        res = chamar(tok, "GET", "commentThreads", params)
        parar = False
        for th in res.get("items", []):
            top = th["snippet"]["topLevelComment"]["snippet"]
            quando = dt.datetime.fromisoformat(top["publishedAt"].replace("Z", "+00:00"))
            if quando < limite:
                parar = True
                break
            if top.get("authorChannelId", {}).get("value") == canal or respondido_pelo_canal(th, canal):
                continue
            saida.append({"commentId": th["id"], "videoId": th["snippet"].get("videoId"),
                          "autor": top.get("authorDisplayName"), "texto": top.get("textDisplay"),
                          "curtidas": top.get("likeCount", 0), "data": top["publishedAt"]})
        pagina = res.get("nextPageToken")
        if parar or not pagina:
            break
    # títulos dos vídeos, para dar contexto à resposta
    ids = sorted({c["videoId"] for c in saida if c["videoId"]})
    titulos = {}
    for i in range(0, len(ids), 50):
        res = chamar(tok, "GET", "videos", {"part": "snippet", "id": ",".join(ids[i:i + 50])})
        titulos.update({v["id"]: v["snippet"]["title"] for v in res.get("items", [])})
    for c in saida:
        c["video"] = titulos.get(c["videoId"], "")
    json.dump(saida, sys.stdout, ensure_ascii=False, indent=2)
    print()


def responder(arquivo):
    tok = token()
    canal = os.environ.get("YT_CHANNEL_ID", CANAL_PADRAO)
    with open(arquivo, encoding="utf-8") as f:
        respostas = json.load(f)
    for r in respostas:
        th = chamar(tok, "GET", "commentThreads", {"part": "snippet,replies", "id": r["commentId"]})
        itens = th.get("items", [])
        if not itens:
            print(f"pulado (comentário sumiu): {r['commentId']}")
            continue
        if respondido_pelo_canal(itens[0], canal):
            print(f"pulado (já respondido): {r['commentId']}")
            continue
        res = chamar(tok, "POST", "comments", {"part": "snippet"},
                     {"snippet": {"parentId": r["commentId"], "textOriginal": r["texto"]}})
        print(f"respondido: {r['commentId']} -> {res.get('id')}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "pendentes":
        dias = int(sys.argv[sys.argv.index("--dias") + 1]) if "--dias" in sys.argv else 7
        pendentes(dias)
    elif len(sys.argv) == 3 and sys.argv[1] == "responder":
        responder(sys.argv[2])
    else:
        sys.exit(__doc__)
