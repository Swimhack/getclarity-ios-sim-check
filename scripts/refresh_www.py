# Test-only: overlay the current public web build (/app/) onto a bundled www dir.
import sys, os, re, urllib.request
www=sys.argv[1]; BASE='https://wayneadamgreer-com.stricklandai.com'
def get(p):
    return urllib.request.urlopen(urllib.request.Request(BASE+p,headers={'User-Agent':'ci'}),timeout=60).read()
def put(p,b):
    f=os.path.join(www,p.lstrip('/')); os.makedirs(os.path.dirname(f),exist_ok=True); open(f,'wb').write(b)
pages={'/app/':'/app/index.html'}
for r in ['journal','profile','explore','reflect','check-in','checkin','download']:
    pages[f'/app/{r}']=f'/app/{r}.html'
idx=get('/app/').decode()
for src,dst in pages.items():
    try: put(dst,get(src))
    except Exception as e: print('skip',src,e)
refs=set(re.findall(r'(?:src|href)="(/app/[^"?]+)',idx))
for r in refs:
    if r.endswith('.js') or r.endswith('.css'): put(r,get(r)); print('got',r)
js=[r for r in refs if '/_expo/' in r and r.endswith('.js')]
for j in js:
    for a in set(re.findall(r'"(/app/assets/[^"]+)"',open(os.path.join(www,j.lstrip('/')),encoding='utf8',errors='ignore').read())):
        if not os.path.exists(os.path.join(www,a.lstrip('/'))):
            try: put(a,get(a)); print('asset',a)
            except Exception as e: print('miss',a,e)
print('bundles',js)
