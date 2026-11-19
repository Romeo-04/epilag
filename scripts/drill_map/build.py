"""Build the drill-down map boundaries (site/public/geo/drill.json, used by the app's forecast map) and the
standalone prototype page (docs/prototypes/forecast-drill/index.html).

Usage: bash scripts/drill_map/boundaries.sh /tmp/ph-geo && python scripts/drill_map/build.py /tmp/ph-geo

Boundaries: PSA PSGC shapefiles as published in faeldon/philippines-json-maps (MIT licence), hi-res pack,
prepared by boundaries.sh. Forecasts, history and barangay case shares come from docs/web/data.
The page is one self-contained HTML file with the data inlined.
"""
import json, math, re, sys
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[2]; R=str(ROOT)+'/'; HI=sys.argv[1]
L=lambda p: json.load(open(p))
meta=L(R+'docs/web/data/meta.json')
regG=L(HI+'/reg_u.json'); proG=L(HI+'/prov_u.json'); bgyG=L(HI+'/bgy_full.json'); mini=L(HI+'/reg_mini.json')
bgyD=L(R+'docs/web/data/qc_barangays.json')
def cols(p):
    d=L(R+p)['cols']; n=len(next(iter(d.values())))
    return [{k:d[k][i] for k in d} for i in range(n)]
def rings(g):
    if g is None: return []
    return [g['coordinates']] if g['type']=='Polygon' else g['coordinates']
pts=[p for f in regG['features'] for poly in rings(f['geometry']) for r in poly for p in r]
def merc(lon,lat): return (lon, math.degrees(math.log(math.tan(math.pi/4+math.radians(lat)/2))))
xs=[merc(*p)[0] for p in pts]; ys=[merc(*p)[1] for p in pts]
x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
W=1000; S=W/(x1-x0); H=(y1-y0)*S
def proj(p):
    x,y=merc(p[0],p[1]); return ((x-x0)*S, (y1-y)*S)
def area(r): return 0.5*sum(r[i][0]*r[i-1][1]-r[i-1][0]*r[i][1] for i in range(len(r)))
def centroid(r):
    A=-area(r)
    if abs(A)<1e-12: return (sum(p[0] for p in r)/len(r), sum(p[1] for p in r)/len(r))
    cx=cy=0
    for i in range(len(r)):
        a,b=r[i-1]; c,d=r[i]; k=a*d-c*b; cx+=(a+c)*k; cy+=(b+d)*k
    return (cx/(6*A), cy/(6*A))
def inside(pt,r):
    x,y=pt; c=False
    for i in range(len(r)):
        xi,yi=r[i]; xj,yj=r[i-1]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi: c=not c
    return c
def labelpt(r):
    c=centroid(r)
    if inside(c,r): return c
    best=None
    b0=min(p[1] for p in r); b1=max(p[1] for p in r)
    for t in [i/20 for i in range(1,20)]:
        y=b0+(b1-b0)*t; xs=[]
        for i in range(len(r)):
            xi,yi=r[i]; xj,yj=r[i-1]
            if (yi>y)!=(yj>y): xs.append((xj-xi)*(y-yi)/(yj-yi)+xi)
        xs.sort()
        for i in range(0,len(xs)-1,2):
            w=xs[i+1]-xs[i]; score=w-abs(y-c[1])*.5
            if best is None or score>best[0]: best=(score,((xs[i]+xs[i+1])/2,y))
    return best[1] if best else c
def shape(g,dec,minhole=12.0):
    polys=[];bb=[1e9,1e9,-1e9,-1e9];big=None;bigA=0
    for poly in rings(g):
        P=[]
        for j,ring in enumerate(poly):
            pr=[proj(p) for p in ring]
            if pr[0]==pr[-1]: pr=pr[:-1]
            if len(pr)<3: continue
            A=abs(area(pr))
            if j>0 and A<minhole: continue
            for x,y in pr: bb=[min(bb[0],x),min(bb[1],y),max(bb[2],x),max(bb[3],y)]
            if j==0 and A>bigA: bigA,big=A,pr
            flat=[]
            for x,y in pr: flat+= [round(x,dec),round(y,dec)]
            P.append(flat)
        if P: polys.append(P)
    lp=labelpt(big)
    return {'polys':polys,'bb':[round(v,4) for v in bb],'c':[round(lp[0],4),round(lp[1],4)],'a':round(bigA,5)}
def fcmap(rows, units):
    out=defaultdict(dict)
    for x in rows:
        u=units[x['u']]
        out[u][x['horizon']]={k:x[k] for k in ('q10','q50','q90','alert','epidemic','level','q50_per100k')}
        out[u]['_wk']=x['week']
    return out
def hist(rows,units,n):
    h=defaultdict(list)
    for x in rows: h[units[x['u']]].append((x['week'],x['cases']))
    return {u:[c for w,c in sorted(v)[-n:]] for u,v in h.items()}, {u:sorted(v)[-1][0] for u,v in h.items()}
RP=meta['panels']['region_qc']; PP=meta['panels']['province']
rfc=fcmap(cols('docs/web/data/region_qc_forecast.json'),RP['units'])
pfc=fcmap(cols('docs/web/data/province_forecast.json'),PP['units'])
rh,rhend=hist(cols('docs/web/data/region_qc_history.json'),RP['units'],26)
ph,phend=hist(cols('docs/web/data/province_history.json'),PP['units'],26)
def nice(name):
    m=re.search(r'\(([^)]+)\)',name); s=m.group(1) if m else name
    return s.replace(' Region','') if s!='National Capital Region' else s
code={'R_NCR':'NCR','R_CAR':'CAR','R_BARMM':'BARMM','R_MIMAROPA':'MIMAROPA'}
rmeta={r['id']:r for r in meta['regions']}
regions=[]
for f in regG['features']:
    u=f['properties']['region']; m=rmeta[u]
    c=code.get(u, m['name'].split(' (')[0])
    regions.append({'id':u,'name':m['name'],'nice':nice(m['name']),'code':c,'tag':code.get(u,c.replace('Region ','')),
        'pop':RP['population'][u],'fc':rfc[u],'hist':rh[u],'histEnd':rhend[u],**shape(f['geometry'],1)})
prov=[]
for f in proG['features']:
    u=f['properties']['unit']; r=f['properties']['region']
    nm=PP['names'].get(u,'Special Geographic Area (BARMM)')
    prov.append({'id':u,'name':nm,'region':r,'pop':PP['population'].get(u),'fc':pfc.get(u),'hist':ph.get(u),'histEnd':phend.get(u),**shape(f['geometry'],2)})
def fix(s):
    try: s=s.encode('latin1').decode('utf8')
    except Exception: pass
    return s
def key(s):
    s=re.sub(r'\s*\(.*\)','',fix(s)).lower().replace('ñ','n')
    return re.sub(r'[^a-z0-9]','',s)
bd={key(x['Barangay']):x for x in bgyD}
rank={key(x['Barangay']):i+1 for i,x in enumerate(sorted(bgyD,key=lambda x:-x['share']))}
feats=bgyG['features']; edges=defaultdict(set)
for i,f in enumerate(feats):
    for poly in rings(f['geometry']):
        for ring in poly:
            for a,b in zip(ring,ring[1:]):
                ka=(round(a[0],6),round(a[1],6)); kb=(round(b[0],6),round(b[1],6))
                if ka!=kb: edges[(min(ka,kb),max(ka,kb))].add(i)
adj=defaultdict(set)
for e,s in edges.items():
    for a in s:
        for b in s:
            if a!=b: adj[a].add(b)
bnd=[e for e,s in edges.items() if len(s)==1]
g=defaultdict(list)
for a,b in bnd: g[a].append(b); g[b].append(a)
used=set(); chains=[]
for a,b in bnd:
    if (a,b) in used: continue
    used|={(a,b),(b,a)}; ch=[a,b]; cur=b
    while True:
        nx=[n for n in g[cur] if (cur,n) not in used]
        if not nx: break
        n=nx[0]; used|={(cur,n),(n,cur)}; ch.append(n); cur=n
        if n==ch[0]: break
    chains.append(ch)
chains.sort(key=len,reverse=True)
print('qc chains',[len(c) for c in chains[:5]],file=sys.stderr)
outline=[]
for ch in chains:
    if len(ch)<30: continue
    fl=[]
    for p in ch: x,y=proj(p); fl+=[round(x,4),round(y,4)]
    outline.append(fl)
bgys=[]
for i,f in enumerate(feats):
    nm=f['properties']['adm4_en']; k=key(nm); d=bd.get(k)
    if not d: print('nomatch',nm,file=sys.stderr); continue
    sh=shape(f['geometry'],4,0) if f['geometry'] else {'polys':None}
    bgys.append({'id':'b'+str(f['properties']['adm4_psgc']),'name':fix(nm),'pcode':d['ADM4_PCODE'],'c22':d['cases_2022_2025'],'c25':d['cases_2025'],
        'share':d['share'],'rank':rank[k],'nbi':sorted(adj[i]),**sh})
ids={i:'b'+str(f['properties']['adm4_psgc']) for i,f in enumerate(feats)}
for b in bgys: b['nb']=[ids[j] for j in b.pop('nbi')]
def svgpath(g):
    out=''
    for poly in rings(g):
        for r in poly:
            pr=[proj(p) for p in r]
            out+='M'+'L'.join('%.0f %.0f'%p for p in pr)+'Z'
    return out
minis={f['properties']['region']:svgpath(f['geometry']) for f in mini['features']}
out={'W':W,'H':round(H,2),'regions':regions,'provinces':prov,'barangays':bgys,'qcOutline':outline,'mini':minis,
  'qc':{'fc':rfc['QC'],'hist':rh['QC'],'histEnd':rhend['QC'],'pop':RP['population']['QC'],'region':'R_NCR'},
  'regionWeek':RP['forecast_week'],'provinceWeek':PP['forecast_week']}
# boundaries only, for the app's forecast map (site/src/lib/drill-map.js); forecasts come from docs/web/data there
GEO_KEYS={'regions':('id','polys','bb','c','a'),'provinces':('id','region','polys','bb','c','a'),'barangays':('id','pcode','name','polys','bb','c','a','nb')}
geo={'W':W,'H':round(H,2),'qcOutline':outline,'mini':minis,**{k:[{f:x[f] for f in fs if f in x} for x in out[k]] for k,fs in GEO_KEYS.items()}}
geo_dest=ROOT/'site/public/geo/drill.json'
geo_dest.write_text(json.dumps(geo,separators=(',',':')))
print('wrote',geo_dest,geo_dest.stat().st_size,'bytes',file=sys.stderr)
s=json.dumps(out,separators=(',',':'))
page=(ROOT/'scripts/drill_map/page.html').read_text().replace('__DATA__',s)
dest=ROOT/'docs/prototypes/forecast-drill/index.html'
dest.write_text('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'+page.replace('<style>','<style>\n[hidden] { display: none !important }\n',1)+'</html>\n')
print('wrote',dest,len(s),'bytes of data',file=sys.stderr)
