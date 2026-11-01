import os, time, json, traceback
from appium import webdriver
from appium.options.ios import XCUITestOptions
B=os.environ['BASE']; U=os.environ['UDID']; R={}
o=XCUITestOptions(); o.udid=U; o.browser_name='Safari'; o.platform_name='iOS'
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
d.set_page_load_timeout(60)
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
R['offline']='not tested (no reliable simulator network toggle)'
json.dump(R,open('out/results.json','w'),indent=1); print(json.dumps(R,indent=1)); d.quit()
