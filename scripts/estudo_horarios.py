"""Estudo de fluxo de comentários: por hora de Brasília e atraso após a publicação."""
import datetime as dt, json, os, sys, collections, statistics
sys.path.insert(0, os.path.dirname(__file__))
import comentarios as c

BRT = dt.timezone(dt.timedelta(hours=-3))
desde = dt.datetime.fromisoformat(sys.argv[1]).replace(tzinfo=BRT) if len(sys.argv) > 1 else dt.datetime(2026, 11, 1, tzinfo=BRT)
tok = c.token()
canal = os.environ.get("YT_CHANNEL_ID", c.CANAL_PADRAO)
itens, pag = [], None
while True:
    p = {"part": "snippet", "allThreadsRelatedToChannelId": canal, "order": "time", "maxResults": 100}
    if pag: p["pageToken"] = pag
    r = c.chamar(tok, "GET", "commentThreads", p)
    stop = False
    for th in r.get("items", []):
        s = th["snippet"]["topLevelComment"]["snippet"]
        t = dt.datetime.fromisoformat(s["publishedAt"].replace("Z", "+00:00"))
        if t < desde: stop = True; break
        if s.get("authorChannelId", {}).get("value") == canal: continue
        itens.append((t, s.get("videoId")))
    pag = r.get("nextPageToken")
    if stop or not pag: break
vids = sorted({v for _, v in itens if v})
pub = {}
for i in range(0, len(vids), 50):
    r = c.chamar(tok, "GET", "videos", {"part": "snippet", "id": ",".join(vids[i:i+50])})
    for v in r["items"]:
        pub[v["id"]] = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
hora = collections.Counter(t.astimezone(BRT).hour for t, _ in itens)
dia = collections.Counter(t.astimezone(BRT).date().isoformat() for t, _ in itens)
atr = [(t - pub[v]).total_seconds() / 3600 for t, v in itens if v in pub]
print("total", len(itens), "desde", desde.date())
print("por hora BRT:", {h: hora[h] for h in sorted(hora)})
print("por dia:", dict(sorted(dia.items())))
if atr:
    atr.sort(); n = len(atr)
    print("atraso h: mediana %.1f p75 %.1f p90 %.1f" % (statistics.median(atr), atr[int(n*.75)], atr[int(n*.9)]))
    print("até 6h: %.0f%%  até 24h: %.0f%%" % (100*sum(a<=6 for a in atr)/n, 100*sum(a<=24 for a in atr)/n))
