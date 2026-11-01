import os, time, json, traceback
from appium import webdriver
from appium.options.ios import XCUITestOptions
U=os.environ['UDID']; BID='com.stricklandai.getclarity'; R={}; V=os.environ.get('VARIANT','')
o=XCUITestOptions(); o.udid=U; o.platform_name='iOS'; o.bundle_id=BID
for k,v in {'noReset':True,'wdaLaunchTimeout':600000,'newCommandTimeout':900,'webviewConnectTimeout':30000,'includeSafariInWebviews':False}.items(): o.set_capability('appium:'+k,v)
d=webdriver.Remote('http://127.0.0.1:4723',options=o)
def ctx():
    for i in range(20):
        w=[c for c in d.contexts if str(c).startswith('WEBVIEW')]
        if w: d.switch_to.context(w[-1]); return True
        time.sleep(2)
    return False
def shot(n):
    c=d.current_context; d.switch_to.context('NATIVE_APP'); d.get_screenshot_as_file(f'out/{V}_{n}.png'); d.switch_to.context(c)
def body(): return d.execute_script('return document.body?document.body.innerText:""')
def go(p): d.execute_script('location.href=arguments[0]',p); time.sleep(6)
def click_text(t):
    return d.execute_script("""const t=arguments[0];const els=[...document.querySelectorAll('*')].filter(e=>e.children.length<3&&e.innerText&&e.innerText.trim()===t);if(!els.length)return false;let e=els[els.length-1];(e.closest('[role=button],button,a')||e).click();return true;""",t)
def native_tap(label):
    d.switch_to.context('NATIVE_APP')
    try:
        els=d.find_elements('accessibility id',label)
        if els: els[-1].click(); return True
        return False
    finally: ctx()
def step(name,fn):
    try: R[name]=fn() or 'pass'
    except Exception as e: R[name]='FAIL: '+repr(e)[:300]; traceback.print_exc()
    print(name,'=>',R[name],flush=True)
    try: shot(name)
    except Exception as e: print('shot err',e)
time.sleep(8)
R['contexts']=str(d.contexts)
if not ctx():
    shot('no_webview'); R['render']='FAIL: no webview context '+R['contexts']
    json.dump(R,open(f'out/{V}_results.json','w'),indent=1); print(R); raise SystemExit
R['location']=d.execute_script('return location.href')
step('render', lambda: 'pass' if len(body())>40 else 'FAIL: body=%r html=%r'%(body()[:100],d.execute_script('return document.documentElement.outerHTML.slice(0,300)')))
step('contact_link', lambda: 'present' if 'contact' in (body()+str(d.execute_script("return [...document.querySelectorAll('a[href]')].map(a=>a.href).join(' ')"))).lower() else 'absent')
MARK='simcheck%d'%int(time.time())
def create():
    go('/app/reflect')
    click_text('Direction')
    tas=d.find_elements('css selector','textarea')
    if not tas: return 'FAIL: no textarea; text='+body()[:300]
    tas[0].send_keys(MARK)
    if len(tas)>1: tas[1].send_keys('step1')
    time.sleep(1)
    for t in ['Save to my journal','Save to journal','Save my reflection','Save']:
        if click_text(t): time.sleep(3); return 'pass (clicked %s) after=%s'%(t,body()[:120].replace('\n',' '))
    return 'FAIL: no save button; text='+body()[:300]
step('journal_create_save',create)
step('journal_listed', lambda: (go('/app/journal'), 'pass' if MARK in body() else 'FAIL: not listed; text='+body()[:300])[1])
def relaunch():
    d.switch_to.context('NATIVE_APP'); d.terminate_app(BID); time.sleep(2); d.activate_app(BID); time.sleep(8)
    if not ctx(): return 'FAIL: no webview after relaunch'
    go('/app/journal'); return 'pass' if MARK in body() else 'FAIL: entry lost after relaunch'
step('persistence_relaunch',relaunch)
def exports():
    go('/app/profile'); out=[]
    for t in ['Download as text','Download as JSON','Print']:
        ok=click_text(t); time.sleep(3); shot('export_'+t.replace(' ','_'))
        d.switch_to.context('NATIVE_APP'); src=d.page_source; ctx()
        sheet=any(k in src for k in ['Share','Save to Files','Print','Options','Cancel'])
        out.append(f'{t}:{"clicked" if ok else "missing"}{"+native sheet" if sheet else ""}')
        for b in ['Cancel','Close','Done']:
            if native_tap(b): break
    return ('pass ' if all('clicked' in x for x in out) else 'FAIL ')+', '.join(out)
step('exports',exports)
def explore():
    go('/app/explore')
    links=d.execute_script("return [...document.querySelectorAll('a[href]')].map(a=>a.href)")
    txt=body()
    want=['the-authority-edge','becoming','clarity-lab','events']
    found=[w for w in want if w in ' '.join(links)]
    return ('pass' if found else 'CHECK')+' links=%s text=%s'%(json.dumps(links[:12]),txt[:200].replace('\n',' '))
step('explore_links',explore)
def offline():
    res=d.execute_script("return performance.getEntriesByType('resource').map(r=>r.name).filter(n=>/^https?:/.test(n))")
    return ('pass (all assets bundled, origin %s)'%d.execute_script('return location.origin')) if not res else 'remote loads: %s'%res[:8]
step('offline_no_remote_assets',offline)
def delete():
    go('/app/journal')
    ok=d.execute_script("const e=[...document.querySelectorAll('[aria-label=\"Delete entry\"]')].pop();if(!e)return false;e.click();return true;")
    if not ok: return 'FAIL: no delete control'
    time.sleep(2); shot('delete_confirm')
    d.switch_to.context('NATIVE_APP'); src=d.page_source
    conf='Delete this entry' in src or 'can’t be undone' in src
    tapped=False
    for b in ['Delete','OK']:
        els=d.find_elements('accessibility id',b)
        if els: els[-1].click(); tapped=True; break
    ctx()
    if not tapped: click_text('Delete')
    time.sleep(3); go('/app/journal')
    return ('pass' if MARK not in body() else 'FAIL: still present')+' native_confirm=%s'%conf
step('journal_delete_confirm',delete)
json.dump(R,open(f'out/{V}_results.json','w'),indent=1); print(json.dumps(R,indent=1)); d.quit()
