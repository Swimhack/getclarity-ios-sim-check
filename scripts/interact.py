import os, time, json, traceback
from appium import webdriver
from appium.options.ios import XCUITestOptions
B=os.environ['BASE']; U=os.environ['UDID']; R={}
NATIVE=os.environ.get('NATIVE')=='1'
o=XCUITestOptions(); o.udid=U; o.platform_name='iOS'
if NATIVE:
    o.bundle_id='com.stricklandai.getclarity'; o.set_capability('appium:noReset',True)
else: o.browser_name='Safari'
o.set_capability('appium:wdaLaunchTimeout',600000); o.set_capability('appium:newCommandTimeout',600)
d=webdriver.Remote('http://127.0.0.1:4723',options=o)
def shot(n): d.get_screenshot_as_file(f'out/int_{n}.png')
def body(): return d.execute_script('return document.body.innerText')
def click_text(t):
    return d.execute_script("""const t=arguments[0];const els=[...document.querySelectorAll('[role=button],button,a,div')].filter(e=>e.innerText&&e.innerText.trim()===t);if(!els.length)return false;els[els.length-1].click();return true;""",t)
def step(name,fn):
    try: R[name]=fn() or 'pass'
    except Exception as e: R[name]='FAIL: '+repr(e)[:300]; traceback.print_exc()
    print(name,R[name]); 
    try: shot(name)
    except: pass
def ctx():
    for i in range(30):
        w=[c for c in d.contexts if c.startswith('WEBVIEW')]
        if w: d.switch_to.context(w[-1]); return
        time.sleep(2)
    raise SystemExit('no webview context: %s'%d.contexts)
if NATIVE:
    time.sleep(10); ctx(); B=d.execute_script('return location.origin'); print('origin',B)
    _get=lambda u: d.execute_script('location.href=arguments[0]',u)
    d.get=_get; d.refresh=lambda: d.execute_script('location.reload()')
    d.get_screenshot_as_file=lambda f:(d.switch_to.context('NATIVE_APP'),webdriver.Remote.get_screenshot_as_file(d,f),ctx())
else: d.set_page_load_timeout(60)
d.get(B+'/app/'); time.sleep(8)
step('render', lambda: 'pass' if len(body())>40 else 'FAIL: empty body')
step('contact_absent', lambda: 'pass' if 'contact' not in body().lower() else 'FAIL: contact text present')
MARK='simcheck-%d'%int(time.time())
def create():
    d.get(B+'/app/reflect'); time.sleep(8)
    tas=d.find_elements('css selector','textarea')
    if not tas: return 'FAIL: no textarea; text='+body()[:300]
    tas[0].send_keys(MARK); time.sleep(1)
    for t in ['Save to my journal','Save to journal','Save my reflection','Save']:
        if click_text(t): break
    else: return 'FAIL: no save button; text='+body()[:300]
    time.sleep(3); return 'pass'
step('journal_create_save',create)
def injournal():
    d.get(B+'/app/journal'); time.sleep(8)
    return 'pass' if MARK in body() else 'FAIL: marker not in journal; text='+body()[:300]
step('journal_listed',injournal)
step('persistence_reload', lambda: (d.refresh(), time.sleep(8), 'pass' if MARK in body() else 'FAIL after reload')[2])
def exports():
    d.get(B+'/app/profile'); time.sleep(8); b=body()
    return 'pass (buttons present)' if 'Download as text' in b and 'Download as JSON' in b else 'FAIL: export buttons missing; text='+b[:300]
step('exports',exports)
def explore():
    d.get(B+'/app/explore'); time.sleep(8)
    links=d.execute_script("return [...document.querySelectorAll('a[href]')].map(a=>a.href)")
    return 'pass: %d links %s'%(len(links),json.dumps(links[:15])) if links else 'FAIL: no links; text='+body()[:200]
step('explore_links',explore)
def delete():
    d.get(B+'/app/journal'); time.sleep(8)
    ok=d.execute_script("const e=document.querySelector('[aria-label=\"Delete entry\"]');if(!e)return false;e.click();return true;")
    if not ok: return 'FAIL: no delete control'
    time.sleep(2)
    try: d.switch_to.alert.accept()
    except Exception: click_text('Delete')
    time.sleep(3); d.refresh(); time.sleep(8)
    return 'pass' if MARK not in body() else 'FAIL: marker still present'
step('journal_delete',delete)
step('sw_registered', lambda: str(d.execute_async_script("const cb=arguments[0];if(!navigator.serviceWorker)return cb('no SW api');navigator.serviceWorker.getRegistrations().then(r=>cb('registrations='+r.length))")))
if NATIVE:
    R['offline']='bundled: origin=%s, remote resources=%s'%(B,d.execute_script("return performance.getEntriesByType('resource').map(r=>r.name).filter(n=>n.startsWith('http')).slice(0,10)"))
    def relaunch():
        d.switch_to.context('NATIVE_APP'); d.terminate_app(o.bundle_id); time.sleep(2); d.activate_app(o.bundle_id); time.sleep(8); ctx()
        return 'relaunch ok'
    step('relaunch',relaunch)
else: R['offline']='not tested (no reliable simulator network toggle)'
json.dump(R,open('out/results.json','w'),indent=1); print(json.dumps(R,indent=1)); d.quit()
