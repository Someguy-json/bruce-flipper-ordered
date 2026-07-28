#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Corrige les themes Flipper_Bruce_By_anonimoKali (menu-liste facon Flipper).
# L'auteur PAGINE par blocs de 4 (pages [1-4][5-8][9-12][13-16], le curseur
# descend dans la page) dans l'ordre NUMERIQUE (wifi,ble,eth,rf,...) != ordre
# reel Bruce -> voisins faux. On reconstruit chaque PNG numerote avec la vraie
# sequence (JSON inchange : wifi=1.png, etc.).
import os, glob, numpy as np
from PIL import Image, ImageDraw

NUM2KEY = {1:"wifi",2:"ble",3:"ethernet",4:"rf",5:"rfid",6:"ir",7:"fm",8:"files",
           9:"gps",10:"nrf",11:"interpreter",12:"lora",13:"others",14:"clock",
           15:"connect",16:"config"}
KEY2NUM = {v:k for k,v in NUM2KEY.items()}
REAL = ["wifi","ble","rf","nrf","lora","fm","ir","ethernet","gps","rfid",
        "files","interpreter","clock","others","config"]     # ordre reel, connect exclu
N = len(REAL)

def bg_of(a): return a[1,1].astype(int)
def fg_mask(a,bg,thr=70): return np.sqrt(((a.astype(int)-bg)**2).sum(2))>thr

def detect_rows(fg, split):
    proj = fg[:, :split].sum(1); thr=max(4,proj.max()*0.15)
    runs=[]; inb=False
    for y,v in enumerate(proj):
        if v>thr and not inb: inb=True; y0=y
        elif v<=thr and inb: inb=False; runs.append((y0,y-1))
    if inb: runs.append((y0,len(proj)-1))
    runs=[r for r in runs if (r[1]-r[0])>=7]
    return [(r[0]+r[1])//2 for r in runs]

def page_start(i):  return ((i-1)//4)*4 + 1     # 1-based
def page_row(i):    return (i-1)%4

def process_folder(folder):
    pngs=sorted(glob.glob(os.path.join(folder,"*.png")))
    if not pngs: return
    ref=np.array(Image.open(pngs[0]).convert("RGB")); Hh,Ww,_=ref.shape
    split=int(Ww*0.575); half=max(9,int(Hh*0.115))
    allc=[]
    for p in pngs:
        a=np.array(Image.open(p).convert("RGB")); c=detect_rows(fg_mask(a,bg_of(a)),split)
        if len(c)==4: allc.append(c)
    centers=[int(np.median([c[r] for c in allc])) for r in range(4)] if allc else \
            [int(Hh*x) for x in (0.13,0.38,0.63,0.88)]
    bg=tuple(int(x) for x in bg_of(ref))
    boxcol=(0,0,0) if sum(bg)>300 else (255,255,255)

    # 1) tuiles : item num recolte depuis une image VOISINE de sa page (non encadree)
    tiles={}
    for num,key in NUM2KEY.items():
        r=page_row(num); ps=page_start(num)
        src = ps if ps!=num else ps+1                 # meme page, curseur ailleurs
        fp=os.path.join(folder,f"{src}.png")
        if not os.path.exists(fp): fp=os.path.join(folder,f"{num}.png")
        a=Image.open(fp).convert("RGB")
        cy=centers[r]
        tiles[key]=a.crop((0, cy-half, split, cy+half))

    # 2) reconstruction dans l'ordre reel (ecrit sous le numero de chaque item)
    for i in range(1,N+1):
        key=REAL[i-1]; num=KEY2NUM[key]
        canvas=Image.open(os.path.join(folder,f"{num}.png")).convert("RGB")
        d=ImageDraw.Draw(canvas)
        clr=int(Ww*0.585)
        d.rectangle([0,0,clr,Hh-1],fill=bg)            # efface la liste (garde le dauphin)
        ps=page_start(i); crow=page_row(i)
        win=[REAL[j] for j in range(ps-1, min(ps+3,N))]
        for r,itk in enumerate(win):
            cy=centers[r]; canvas.paste(tiles[itk],(0,cy-half))
        cy=centers[crow]                                # cadre ligne active
        for t in range(2):
            d.rectangle([2+t,cy-half+t,split-6-t,cy+half-t],outline=boxcol)
        canvas.save(os.path.join(folder,f"{num}.png"))

if __name__=="__main__":
    import sys; process_folder(sys.argv[1]); print("done",sys.argv[1])
