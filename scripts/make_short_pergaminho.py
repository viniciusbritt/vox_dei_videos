import numpy as np, subprocess, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S="/tmp/claude-0/-home-claude/eb4f6bdb-551c-5872-8e2f-d4805042a7d6/scratchpad"
O=S+"/short1/v2_"
W,H,FPS,DUR=1080,1920,30,16
rng=np.random.default_rng(3)
# parchment background
BW,BH=int(W*1.05),int(H*1.05)
base=np.array([244,230,198],np.float32)
n=rng.normal(0,1,(BH//8,BW//8)).astype(np.float32)
n=np.asarray(Image.fromarray(((n*30)+128).clip(0,255).astype(np.uint8)).resize((BW,BH),Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))).astype(np.float32)-128
fine=rng.normal(0,6,(BH,BW)).astype(np.float32)
y=np.linspace(-1,1,BH)[:,None]; x=np.linspace(-1,1,BW)[None,:]
vig=np.clip(1-0.30*((x*1.0)**2+(y*0.85)**2)**1.4,0.45,1)
bg=(base[None,None,:]+n[...,None]*0.35+fine[...,None])
bg=bg*vig[...,None]+np.array([92,52,22],np.float32)*(1-vig[...,None])
# stains
for _ in range(10):
    cx,cy=rng.uniform(-1,1),rng.uniform(-1,1); r=rng.uniform(0.1,0.35)
    d=np.exp(-(((x-cx)**2+(y-cy)**2)/r**2))
    bg*= (1-0.04*d)[...,None]
BG=np.clip(bg,0,255).astype(np.uint8)

F=S+"/fonts/"
f_hook=ImageFont.truetype(F+"lora-italic.ttf",50)
f_deus=ImageFont.truetype(F+"cinzel-bold.ttf",150)
f_body=ImageFont.truetype(F+"lora-medium.ttf",48)
f_ref=ImageFont.truetype(F+"mont-semibold.ttf",34)
f_cta=ImageFont.truetype(F+"mont-semibold.ttf",40)
INK=(30,22,16); BROWN=(110,62,28); RED=(128,36,20)
blocks=[
 (0.15,["Você pediu um sinal de"],f_hook,BROWN,6),
 (0.15,["DEUS?"],f_deus,RED,22),
 (0.15,["Aqui está."],f_hook,BROWN,64),
 (0.9,["Senhor, cria em mim","um coração puro e renova","em mim um espírito firme.","Lava-me de toda culpa,","purifica-me dos meus pecados","e não afastes de mim o teu Espírito."],f_body,INK,34),
 (1.7,["Devolve-me a alegria da salvação.","Tira do meu coração toda mágoa,","todo medo e toda inveja,","e enche-o com o teu amor.","Em nome de Jesus, amém."],f_body,INK,46),
 (2.4,["SALMO 51,12-14"],f_ref,BROWN,0),
]
LH=lambda f:int(f.size*(1.05 if f is f_deus else 1.5))
total=sum(LH(f)*len(l)+g for _,l,f,_,g in blocks)
yy=(H-total)//2-150
layers=[]
for st,lines,f,col,g in blocks:
    L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    for ln in lines:
        assert d.textlength(ln,font=f)<=830, ln
        w=d.textlength(ln,font=f); d.text(((W-w)/2,yy),ln,font=f,fill=col+(255,)); yy+=LH(f)
    if lines==["Aqui está."]:
        d.line([(W/2-90,yy+18),(W/2+90,yy+18)],fill=BROWN+(180,),width=2)
    yy+=g
    layers.append((st,np.asarray(L).astype(np.float32)))
C=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(C)
cta="Escreva AMÉM se você recebe esta oração"
w=d.textlength(cta,font=f_cta)
d.rounded_rectangle([(W-w)/2-36,yy+60,(W+w)/2+36,yy+145],radius=42,fill=(70,38,18,235))
d.text(((W-w)/2,yy+75),cta,font=f_cta,fill=(246,232,200,255))
layers.append((3.2,np.asarray(C).astype(np.float32)))

vid=O+"_v.mp4"
ff=subprocess.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
 "-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-preset","medium",vid],stdin=subprocess.PIPE)
for i in range(FPS*DUR):
    t=i/FPS; z=1.0+0.04*t/DUR
    cw,ch=int(BW/z/1.05*1.0*1.0),int(BH/z/1.05)
    cw,ch=int(W*1.05/z/1.0),int(H*1.05/z)
    cw,ch=min(cw,BW),min(ch,BH)
    x0,y0=(BW-cw)//2,(BH-ch)//2
    fr=np.asarray(Image.fromarray(BG[y0:y0+ch,x0:x0+cw]).resize((W,H),Image.BILINEAR)).astype(np.float32)
    for st,Lr in layers:
        if t<st: continue
        a=min(1,(t-st)/0.8); a=a*a*(3-2*a)
        al=Lr[...,3:4]/255*a; fr=fr*(1-al)+Lr[...,:3]*al
    fr*=min(1,t/0.3+0.0001)
    ff.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes())
    if i==FPS*8: Image.fromarray(np.clip(fr,0,255).astype(np.uint8)).save(O+"preview.png")
ff.stdin.close(); ff.wait()

# soft generated piano (royalty-free placeholder)
sr=44100; N=sr*DUR; out=np.zeros(N)
def note(f,t0,dur=3.5,amp=0.18):
    s=int(t0*sr); n=min(int(dur*sr),N-s); tt=np.arange(n)/sr
    env=np.exp(-tt*1.6)*(1-np.exp(-tt*200))
    sig=sum(a*np.sin(2*np.pi*f*k*tt) for k,a in [(1,1),(2,0.35),(3,0.12),(4,0.05)])
    out[s:s+n]+=amp*env*sig
mid=lambda m:440*2**((m-69)/12)
prog=[[57,64,69,72],[53,60,65,69],[48,55,60,64],[55,62,67,71]]  # Am F C G
t0=0.2
for bar in range(4):
    ch=prog[bar%4]
    note(mid(ch[0]-12),t0,4.0,0.22)
    for j,m in enumerate([ch[1],ch[2],ch[3],ch[2],ch[3]+12 if bar%2 else ch[3],ch[2]]):
        note(mid(m),t0+j*0.62,3.0,0.12)
    t0+=3.9
# simple reverb
for d,g in [(0.11,0.35),(0.23,0.25),(0.37,0.18),(0.53,0.12)]:
    k=int(d*sr); out[k:]+=g*out[:-k]
fade=np.ones(N); fl=int(1.5*sr); fade[-fl:]=np.linspace(1,0,fl); out*=fade
out=out/np.abs(out).max()*0.6
st=np.stack([out,np.roll(out,int(0.012*sr))],1)
with wave.open(O+"_piano.wav","wb") as w_:
    w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(sr); w_.writeframes((st*32767).astype(np.int16).tobytes())
