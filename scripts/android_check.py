import subprocess as sp, re, time, json, html, os
V=os.environ.get('VARIANT','x')
PKG='com.stricklandai.getclarity'; R={}; n=[0]
def sh(c): return sp.run('adb shell '+c,shell=True,capture_output=True,text=True).stdout
def shot(name):
    n[0]+=1; sp.run(f'adb exec-out screencap -p > out/{V}_{n[0]:02d}_{name}.png',shell=True)
def dump():
    sh('uiautomator dump /sdcard/u.xml >/dev/null'); x=sp.run('adb exec-out cat /sdcard/u.xml',shell=True,capture_output=True,text=True).stdout
    return x
def nodes(x):
    for m in re.finditer(r'<node [^>]*>',x):
        a=dict(re.findall(r'(\S+?)="([^"]*)"',m.group(0)))
        yield html.unescape(a.get('text','')),html.unescape(a.get('content-desc','')),a
def alltext(): return ' | '.join(t or d for t,d,_ in nodes(dump()) if t or d)
def tap(label,exact=False,last=False):
    hits=[]
    for t,d,a in nodes(dump()):
        for s in (t,d):
            if s and ((s==label) if exact else (label.lower() in s.lower())): hits.append(a)
    if not hits: return False
    a=hits[-1] if last else hits[0]
    x1,y1,x2,y2=map(int,re.findall(r'\d+',a['bounds'])); sh(f'input tap {(x1+x2)//2} {(y1+y2)//2}'); time.sleep(2); return True
def edits():
    out=[]
    for t,d,a in nodes(dump()):
        if 'EditText' in a.get('class',''): out.append(a)
    return out
def tapnode(a):
    x1,y1,x2,y2=map(int,re.findall(r'\d+',a['bounds'])); sh(f'input tap {(x1+x2)//2} {(y1+y2)//2}'); time.sleep(1)
W,H=map(int,re.findall(r'(\d+)x(\d+)',sh('wm size'))[-1])
def swipe_up(): sh(f'input swipe {W//2} {int(H*.8)} {W//2} {int(H*.3)} 300'); time.sleep(1)
def find_scroll(label,tries=5):
    for i in range(tries):
        if tap(label): return True
        swipe_up()
    return False
def launch(): sh(f'monkey -p {PKG} -c android.intent.category.LAUNCHER 1'); time.sleep(10)
def step(name,fn):
    try: R[name]=fn() or 'pass'
    except Exception as e: R[name]='FAIL: '+repr(e)[:200]
    print(name,R[name],flush=True); shot(name)
    open(f'out/{V}_ui_{name}.txt','w').write(alltext())
sh('pm uninstall '+PKG); print(sp.run('adb install -r app.apk',shell=True,capture_output=True,text=True))
R['android']=sh('getprop ro.build.version.release').strip()
launch(); step('render', lambda: 'pass' if len(alltext())>40 else 'FAIL: little text: '+alltext())
step('contact_link', lambda: 'present' if 'contact' in alltext().lower() else 'absent')
MARK='simcheck%d'%int(time.time())
def nav(tab):
    if not tap(tab,exact=True,last=True): tap(tab,last=True)
    time.sleep(2)
def create():
    nav('Reflect'); time.sleep(2)
    tap('Direction')  # focus choice if present
    e=edits()
    if not e: swipe_up(); e=edits()
    if not e: return 'FAIL: no EditText: '+alltext()[:300]
    tapnode(e[0]); sh(f'input text {MARK}'); sh('input keyevent 111'); time.sleep(1)
    e=edits()
    if len(e)>1: tapnode(e[1]); sh('input text step1'); sh('input keyevent 111'); time.sleep(1)
    for t in ['Save my reflection','Save to my journal','Save to journal']:
        if find_scroll(t,3): break
    else: return 'FAIL: no save: '+alltext()[:300]
    time.sleep(2); return 'pass'
step('journal_create_save',create)
def listed():
    nav('Journal'); return 'pass' if MARK in alltext() else 'FAIL: not in journal: '+alltext()[:300]
step('journal_listed',listed)
def persist():
    sh(f'am force-stop {PKG}'); launch(); nav('Journal')
    return 'pass' if MARK in alltext() else 'FAIL after relaunch'
step('persistence_relaunch',persist)
def offline():
    sh('svc wifi disable'); sh('svc data disable'); sh(f'am force-stop {PKG}'); launch(); nav('Journal')
    r='pass' if MARK in alltext() else 'FAIL offline: '+alltext()[:200]
    return r
step('offline_relaunch',offline)
sh('svc wifi enable'); sh('svc data enable')
def exports():
    nav('Profile'); time.sleep(1); out=[]
    for t in ['Download as text','Download as JSON','Print']:
        ok=find_scroll(t); out.append(f'{t}:{"tapped" if ok else "missing"}'); shot('export_'+t.replace(' ','_')); sh('input keyevent 4') if ok else None; time.sleep(2)
        if PKG not in sh('dumpsys window | grep mCurrentFocus'): launch(); nav('Profile')
    return ('pass ' if all('tapped' in o for o in out) else 'FAIL ')+', '.join(out)
step('exports',exports)
def explore():
    launch(); nav('Explore'); txt=alltext(); want=['Authority','Becoming','Clarity Lab','Events']; f=[w for w in want if w.lower() in txt.lower()]; return ('pass ' if f else 'FAIL ')+str(f)+' '+txt[:300]
step('explore',explore)
def explore_tap():
    ok=tap('Authority') ; time.sleep(4); f=sh('dumpsys window | grep mCurrentFocus').strip(); sh('input keyevent 4'); return ('pass' if ok else 'FAIL no Authority button')+' focus='+f
step('explore_link_opens',explore_tap)
def delete():
    launch(); nav('Journal')
    if not find_scroll('Delete entry',3): return 'FAIL: no delete control: '+alltext()[:200]
    shot('delete_confirm'); confirm=alltext()
    tap('Delete',exact=True,last=True); time.sleep(2)
    sh(f'am force-stop {PKG}'); launch(); nav('Journal')
    return ('pass' if MARK not in alltext() else 'FAIL still present')+' confirm_text='+confirm[:150]
step('journal_delete_confirm',delete)
json.dump(R,open(f'out/{V}_results.json','w'),indent=1); print(json.dumps(R,indent=1))
