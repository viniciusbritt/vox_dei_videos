import os,json,urllib.request,urllib.parse,re
D="/mnt/project-files/longos/2026-11-11-terco-misericordia/"
d=urllib.parse.urlencode({"client_id":os.environ["YT_CLIENT_ID"],"client_secret":os.environ["YT_CLIENT_SECRET"],"refresh_token":os.environ["YT_REFRESH_TOKEN"],"grant_type":"refresh_token"}).encode()
tok=json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token",d))["access_token"]
txt=open(D+"youtube-titulo-descricao.txt",encoding="utf-8").read()
title=txt.split("TÍTULO\n")[1].split("\n")[0].strip()
desc=txt.split("DESCRIÇÃO\n")[1].split("\nTAGS")[0].strip()
tags=[t.strip() for t in txt.split('"Tags" do YouTube Studio)\n')[1].split("\n")[0].split(",")]
body={"snippet":{"title":title,"description":desc,"tags":tags,"categoryId":"22","defaultLanguage":"pt-BR","defaultAudioLanguage":"pt-BR"},
 "status":{"privacyStatus":"private","publishAt":"2026-11-11T17:50:00Z","selfDeclaredMadeForKids":False,"containsSyntheticMedia":True}}
vid=D+"terco-misericordia-2026-11-11.mp4"; size=os.path.getsize(vid)
req=urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",data=json.dumps(body).encode(),
 headers={"Authorization":"Bearer "+tok,"Content-Type":"application/json; charset=UTF-8","X-Upload-Content-Type":"video/mp4","X-Upload-Content-Length":str(size)},method="POST")
loc=urllib.request.urlopen(req).headers["Location"]
req=urllib.request.Request(loc,data=open(vid,"rb").read(),headers={"Authorization":"Bearer "+tok,"Content-Type":"video/mp4"},method="PUT")
r=json.load(urllib.request.urlopen(req,timeout=900)); vid_id=r["id"]
print("id",vid_id,json.dumps(r.get("status")))
th=open(D+"thumb-terco-2026-11-11.png","rb").read()
try:
  req=urllib.request.Request(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid_id}",data=th,headers={"Authorization":"Bearer "+tok,"Content-Type":"image/png"},method="POST")
  print("thumb ok", urllib.request.urlopen(req).status)
except urllib.error.HTTPError as e: print("thumb erro", e.code, e.read()[:300])
