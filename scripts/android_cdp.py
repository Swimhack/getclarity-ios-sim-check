import subprocess as sp, time, json, os, sys, urllib.request, re
sys.path.insert(0,'scripts'); import checks, websocket
PKG='com.stricklandai.getclarity'; V=os.environ.get('VARIANT','x'); R={}; n=[0]
def sh(c): return sp.run('adb shell '+c,shell=True,capture_output=True,text=True).stdout
def shot(name):
    n[0]+=1; sp.run(f'adb exec-out screencap -p > out/{V}_{n[0]:02d}_{name}.png',shell=True)
def launch(): sh(f'monkey -p {PKG} -c android.intent.category.LAUNCHER 1'); time.sleep(10)
W={}
def connect():
    try: W['ws'].close()
    except Exception: pass
    time.sleep(3)
    for i in range(20):
        pid=sh(f'pidof {PKG}').strip()
        if pid:
            sp.run(f'adb forward tcp:9222 localabstract:webview_devtools_remote_{pid}',shell=True)
            try:
                pages=[p for p in json.load(urllib.request.urlopen('http://127.0.0.1:9222/json')) if p.get('type')=='page']
                if pages: W['ws']=websocket.create_connection(pages[0]['webSocketDebuggerUrl'],timeout=30,suppress_origin=True); W['id']=0; return True
            except Exception as e: print('cdp wait',e)
        time.sleep(2)
    return False
def js(code,_r=3):
    try: return _js(code)
    except Exception as e:
        if _r<=0: raise
        print('cdp reconnect',e); time.sleep(4); connect(); return js(code,_r-1)
def _js(code):
    W['id']+=1; W['ws'].send(json.dumps({'id':W['id'],'method':'Runtime.evaluate','params':{'expression':code,'returnByValue':True,'awaitPromise':True,'userGesture':True}}))
    while True:
        m=json.loads(W['ws'].recv())
        if m.get('id')==W['id']: return m.get('result',{}).get('result',{}).get('value')
def relaunch():
    sh(f'am force-stop {PKG}'); launch(); connect()
def offline(on):
    s='disable' if on else 'enable'; sh(f'svc wifi {s}'); sh(f'svc data {s}'); time.sleep(3)
def dismiss():
    f=sh('dumpsys window | grep mCurrentFocus')
    if PKG+'/' not in f or 'Print' in f: sh('input keyevent 4'); time.sleep(2)
    if PKG not in sh('dumpsys window | grep mCurrentFocus'): launch(); connect()
sh('pm uninstall '+PKG); print(sp.run('adb install app.apk',shell=True,capture_output=True,text=True).stdout)
R['android']=sh('getprop ro.build.version.release').strip()
launch(); shot('launch')
if connect():
    R['online_net']=sh('ping -c1 -W2 8.8.8.8 | tail -1').strip()
    checks.run({'js':js,'go':lambda p: js('location.href=%s'%json.dumps(p)),'relaunch':relaunch,'shot':shot,'offline':offline,'dismiss':dismiss},R,'simcheck%d'%int(time.time()))
else: R['render']='FAIL: no devtools socket'
json.dump(R,open(f'out/{V}_results.json','w'),indent=1); print(json.dumps(R,indent=1))
