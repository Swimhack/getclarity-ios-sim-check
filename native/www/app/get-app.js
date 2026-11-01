(function(){
  try{
    var w=window,n=navigator,ua=n.userAgent||'';
    var isCap=!!(w.Capacitor&&(w.Capacitor.isNativePlatform?w.Capacitor.isNativePlatform():true))||/Capacitor|; wv\)/.test(ua);
    var standalone=(w.matchMedia&&w.matchMedia('(display-mode: standalone)').matches)||n.standalone===true;
    if(isCap||standalone)return;
    var isIOS=/iPad|iPhone|iPod/.test(ua)||(n.platform==='MacIntel'&&n.maxTouchPoints>1);
    var isAndroid=/Android/i.test(ua);
    var isSafari=isIOS&&/Safari/.test(ua)&&!/CriOS|FxiOS|EdgiOS|OPiOS|GSA\//.test(ua);
    var deferred=null;
    w.addEventListener('beforeinstallprompt',function(e){e.preventDefault();deferred=e;var b=document.querySelectorAll('[data-gc-pwa]');for(var i=0;i<b.length;i++)b[i].hidden=false;});
    w.gcInstallPWA=function(){if(!deferred)return;deferred.prompt();deferred.userChoice.finally(function(){deferred=null;});};
    w.gcEnv={isIOS:isIOS,isAndroid:isAndroid,isSafari:isSafari};
    if(location.pathname.replace(/\/$/,'')==='/app/download')return; // download page renders its own UI
    if(sessionStorage.getItem('gc-getapp-dismissed'))return;
    function mount(){
      var d=document.createElement('div');d.className='gc-getapp';d.setAttribute('role','region');d.setAttribute('aria-label','Get the app');
      d.innerHTML='<img src="/app/icons/icon-192.png" alt="" width="36" height="36">'+
        '<div class="gc-txt"><strong>Get the app</strong><span>'+(isIOS?'Add Get Clarity to your Home Screen':isAndroid?'Install Get Clarity on Android':'Get Clarity on iPhone & Android')+'</span></div>'+
        '<a class="gc-btn" href="/app/download/">Get it</a><button class="gc-x" aria-label="Dismiss">\u00d7</button>';
      d.querySelector('.gc-x').onclick=function(){sessionStorage.setItem('gc-getapp-dismissed','1');d.remove();document.documentElement.classList.remove('gc-has-getapp');};
      document.body.appendChild(d);document.documentElement.classList.add('gc-has-getapp');
    }
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
  }catch(e){}
})();
(function(){try{
  if(location.pathname.replace(/\/$/,'')==='/app/download')return;
  function bar(){if(document.querySelector('.wag-bar'))return;
    var h=document.createElement('header');h.className='wag-bar';
    h.innerHTML='<a href="https://wayneadamgreer.com/" target="_blank" rel="noopener" aria-label="Wayne Adam Greer"><img src="/app/wag-logo.png" alt="Wayne Adam Greer" width="153" height="30"></a>';
    document.body.insertBefore(h,document.body.firstChild);document.documentElement.classList.add('wag-has-bar');}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bar);else bar();
}catch(e){}})();
