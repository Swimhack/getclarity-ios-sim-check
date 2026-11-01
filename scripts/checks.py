# Shared web-content checks. env: js(code)->value, go(path), relaunch(), shot(name), offline(on)
import time, json
SET="""(el,v)=>{const p=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(p,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));}"""
CLICK="""(t)=>{const els=[...document.querySelectorAll('[role=button],button,a,[tabindex]')].filter(e=>e.innerText&&e.innerText.trim().replace(/\\s+/g,' ').startsWith(t));if(!els.length)return false;els[els.length-1].scrollIntoView();els[els.length-1].click();return true;}"""
def run(E, R, mark):
    js=E['js']
    body=lambda: js('document.body?document.body.innerText:""') or ''
    click=lambda t: js('(%s)(%s)'%(CLICK,json.dumps(t)))
    def go(p): E['go'](p); time.sleep(5)
    def step(name,fn):
        try: R[name]=fn() or 'pass'
        except Exception as e: R[name]='FAIL: '+repr(e)[:250]
        print(name,'=>',R[name],flush=True)
        try: E['shot'](name)
        except Exception as e: print('shot err',e)
    R['location']=js('location.href')
    step('render', lambda: 'pass' if 'clarity' in body().lower() else 'FAIL: body=%r'%body()[:150])
    links=lambda: js("[...document.querySelectorAll('a[href]')].map(a=>a.href)") or []
    def create():
        go('/app/reflect'); click('Direction'); time.sleep(1)
        n=js("document.querySelectorAll('textarea').length")
        if not n: return 'FAIL: no textarea'
        js("(()=>{const s=%s;const t=document.querySelectorAll('textarea');s(t[0],%s);if(t[1])s(t[1],'step-one');})()"%(SET,json.dumps(mark)))
        time.sleep(1)
        if not click('Save my reflection'): return 'FAIL: no save button'
        time.sleep(3); return 'pass; after-save text: '+body()[:150].replace('\n',' ')
    step('journal_create_save',create)
    step('journal_listed', lambda: (go('/app/journal'), 'pass' if mark in body() else 'FAIL: not listed: '+body()[:200].replace('\n',' '))[1])
    def persist():
        E['relaunch'](); go('/app/journal'); return 'pass' if mark in body() else 'FAIL: lost after relaunch'
    step('persistence_relaunch',persist)
    def offline():
        if not E.get('offline'): 
            res=js("performance.getEntriesByType('resource').map(r=>r.name).filter(n=>/^https?:/.test(n))") or []
            return ('pass (no network toggle; zero remote requests, origin %s)'%js('location.origin')) if not res else 'remote loads: %s'%res[:6]
        E['offline'](True); E['relaunch'](); go('/app/journal'); ok=mark in body() and 'clarity' in body().lower()
        E['offline'](False); return 'pass (network off, relaunch, entry visible)' if ok else 'FAIL offline: '+body()[:150]
    step('offline',offline)
    def exports():
        go('/app/journal'); out=[]
        js("window.__dl=[];const o=URL.createObjectURL;URL.createObjectURL=b=>{window.__dl.push(b.size+':'+b.type);return o(b)};window.__pr=0;")
        for t in ['Download as text','Download as JSON','Print']:
            ok=click(t); time.sleep(3); E['shot']('export_'+t.replace(' ','_')); out.append('%s:%s'%(t,'clicked' if ok else 'missing'))
            if E.get('dismiss'): E['dismiss']()
        out.append('blobs=%s'%js('window.__dl'))
        out.append('msg=%s'%[l for l in body().split('\n') if 'print' in l.lower() or 'download' in l.lower()][:4])
        return ('pass ' if all('clicked' in x for x in out[:3]) else 'FAIL ')+'; '.join(out)
    step('exports',exports)
    def explore():
        go('/app/explore'); L=links(); b=body()
        want=['the-authority-edge','becoming','clarity-lab','events']
        got=[w for w in want if w in ' '.join(L)]
        btns=[w for w in ['Authority','Becoming','Clarity Lab','Events'] if w.lower() in b.lower()]
        return ('pass' if got or btns else 'FAIL')+' hrefs=%s buttons=%s'%(got,btns)
    step('explore_links',explore)
    step('contact_link', lambda: 'present: '+str([l for l in links() if 'mailto' in l or 'contact' in l]) if any('mailto' in l or 'contact' in l for l in links()) or 'contact' in body().lower() else 'absent (no contact link/text on Explore)')
    def delete():
        go('/app/journal')
        ok=js("(()=>{const e=[...document.querySelectorAll('[aria-label=\"Delete entry\"]')].pop();if(!e)return false;e.click();return true})()")
        if not ok: return 'FAIL: no delete control'
        time.sleep(1); conf='Delete this entry' in body(); E['shot']('delete_confirm')
        if not click('Yes, delete entry'): return 'FAIL: no confirm button (confirm text shown=%s)'%conf
        time.sleep(2); E['relaunch'](); go('/app/journal')
        return ('pass' if mark not in body() else 'FAIL: still present')+' confirm_shown=%s'%conf
    step('journal_delete_confirm',delete)
    return R
