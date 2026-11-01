import os, time, json, sys
sys.path.insert(0,'scripts'); import checks
from appium import webdriver
from appium.options.ios import XCUITestOptions
U=os.environ['UDID']; BID='com.stricklandai.getclarity'; V=os.environ.get('VARIANT',''); R={}
o=XCUITestOptions(); o.udid=U; o.platform_name='iOS'; o.bundle_id=BID
for k,v in {'noReset':True,'wdaLaunchTimeout':600000,'newCommandTimeout':900,'additionalWebviewBundleIds':['*'],'webviewConnectRetries':60}.items(): o.set_capability('appium:'+k,v)
d=webdriver.Remote('http://127.0.0.1:4723',options=o)
def ctx():
    for i in range(30):
        w=[c for c in d.contexts if str(c).startswith('WEBVIEW')]
        if w: d.switch_to.context(w[-1]); return True
        time.sleep(2)
    return False
def shot(n):
    c=d.current_context; d.switch_to.context('NATIVE_APP'); d.get_screenshot_as_file(f'out/{V}_{n}.png')
    if c!='NATIVE_APP': d.switch_to.context(c)
def relaunch():
    d.switch_to.context('NATIVE_APP'); d.terminate_app(BID); time.sleep(2); d.activate_app(BID); time.sleep(8); ctx()
def sheet():
    c=d.current_context; d.switch_to.context('NATIVE_APP'); src=d.page_source
    if c!='NATIVE_APP': d.switch_to.context(c)
    return any(k in src for k in ['ActivityListView','UIActivityContentView','Save to Files','Print','Copy'])
def dismiss():
    c=d.current_context; d.switch_to.context('NATIVE_APP')
    for b in ['Close','Cancel','Done']:
        e=d.find_elements('accessibility id',b)
        if e: e[-1].click(); time.sleep(1); break
    if c!='NATIVE_APP': d.switch_to.context(c)
time.sleep(8); R['contexts']=str(d.contexts)
if ctx():
    E={'js':lambda c: d.execute_script('return '+c), 'go':lambda p: d.execute_script('location.href=arguments[0]',p),'relaunch':relaunch,'shot':shot,'dismiss':dismiss,'sheet':sheet}
    checks.run(E,R,'simcheck%d'%int(time.time()))
else: shot('no_webview'); R['render']='FAIL: no webview context'
json.dump(R,open(f'out/{V}_results.json','w'),indent=1); print(json.dumps(R,indent=1))
