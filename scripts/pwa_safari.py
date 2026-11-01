import os, time, json, sys, subprocess as sp
sys.path.insert(0,'scripts'); import checks
from appium import webdriver
from appium.options.ios import XCUITestOptions
U=os.environ['UDID']; B='https://wayneadamgreer-com.stricklandai.com'; R={}; V='pwa'
o=XCUITestOptions(); o.udid=U; o.platform_name='iOS'; o.browser_name='Safari'
for k,v in {'wdaLaunchTimeout':600000,'newCommandTimeout':900,'safariInitialUrl':B+'/app/'}.items(): o.set_capability('appium:'+k,v)
d=webdriver.Remote('http://127.0.0.1:4723',options=o); d.set_page_load_timeout(60)
def shot(n):
    c=d.current_context; d.switch_to.context('NATIVE_APP'); d.get_screenshot_as_file(f'out/{V}_{n}.png'); d.switch_to.context(c)
def web():
    for c in d.contexts:
        if str(c).startswith('WEBVIEW'): d.switch_to.context(c); return
def sheet():
    c=d.current_context; d.switch_to.context('NATIVE_APP'); src=d.page_source; d.switch_to.context(c)
    return any(k in src for k in ['Download','ActivityListView','Save to Files','Print','Options','View'])
def dismiss():
    c=d.current_context; d.switch_to.context('NATIVE_APP')
    for b in ['Close','Cancel','Done']:
        e=d.find_elements('accessibility id',b)
        if e: e[-1].click(); time.sleep(1); break
    d.switch_to.context(c)
def relaunch(): d.refresh(); time.sleep(6)
d.get(B+'/app/'); time.sleep(8); web()
J=lambda c: d.execute_script('return '+c)
AJ=lambda c: d.execute_async_script('const cb=arguments[arguments.length-1];Promise.resolve('+c+').then(v=>cb(v),e=>cb("ERR "+e))')
R['manifest']=AJ("fetch('/app/manifest.webmanifest').then(r=>r.json()).then(m=>m.display+' '+m.start_url+' icons='+m.icons.length)")
R['apple_meta']=J("[...document.querySelectorAll('meta[name^=apple],link[rel=apple-touch-icon]')].map(e=>(e.name||e.rel)+'='+(e.content||e.href)).join(' | ')")
R['sw_ready']=AJ("navigator.serviceWorker.ready.then(r=>'scope='+r.scope+' active='+!!r.active)")
time.sleep(5); d.refresh(); time.sleep(6)
R['sw_controller']=J("navigator.serviceWorker.controller?navigator.serviceWorker.controller.scriptURL:'none'")
R['cache_count']=AJ("caches.keys().then(k=>Promise.all(k.map(n=>caches.open(n).then(c=>c.keys()).then(x=>n+':'+x.length)))).then(a=>a.join(','))")
# visit routes once online so navigations are cached too
for p in ['/app/journal','/app/reflect','/app/explore','/app/profile']: d.get(B+p); time.sleep(4)
web(); d.get(B+'/app/'); time.sleep(4)
checks.run({'js':J,'go':lambda p: d.get(B+p),'relaunch':relaunch,'shot':shot,'sheet':sheet,'dismiss':dismiss},R,'pwacheck%d'%int(time.time()))
# offline: blackhole the host on the macOS runner (simulator shares host networking)
sp.run("echo '0.0.0.0 wayneadamgreer-com.stricklandai.com' | sudo tee -a /etc/hosts >/dev/null; sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder",shell=True)
time.sleep(3)
R['offline_probe']=AJ("fetch('/app/manifest.webmanifest?nocache='+Date.now(),{cache:'no-store'}).then(r=>'reachable '+r.status).catch(e=>'blocked: '+e)")
res={}
for p in ['/app/','/app/journal','/app/explore']:
    try: d.get(B+p); time.sleep(5); web(); t=J("document.body.innerText"); res[p]='ok' if 'clarity' in t.lower() else 'blank/err: '+t[:80]
    except Exception as e: res[p]='ERR '+repr(e)[:100]
    shot('offline'+p.replace('/','_'))
R['offline_reload']=('pass ' if all(v=='ok' for v in res.values()) else 'FAIL ')+json.dumps(res)
json.dump(R,open('out/pwa_results.json','w'),indent=1); print(json.dumps(R,indent=1))
