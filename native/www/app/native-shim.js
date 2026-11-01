/* Get Clarity native shim: only active inside the Capacitor app. Routes exports/print to the native share sheet. */
(function(){
  var C=window.Capacitor; if(!C||!C.isNativePlatform||!C.isNativePlatform())return;
  function P(n){return C.Plugins&&C.Plugins[n];}
  function b64(s){return btoa(unescape(encodeURIComponent(s)));}
  async function shareText(name,text,title){
    var FS=P('Filesystem'),SH=P('Share');
    var r=await FS.writeFile({path:name,data:b64(text),directory:'CACHE'});
    window.__gcLastShare={name:name,uri:r.uri,bytes:text.length,at:Date.now()};
    await SH.share({title:title||name,dialogTitle:title||name,files:[r.uri]});
  }
  window.__gcShareText=shareText;
  // text/JSON downloads: the app uses navigator.share({files}) when Capacitor is present
  try{
    navigator.canShare=function(d){return !!(d&&d.files&&d.files.length);};
    navigator.share=async function(d){
      var f=d.files[0]; var t=await f.text(); return shareText(f.name,t,d.title);
    };
  }catch(e){}
  // fallback: <a download href=blob:...>.click()
  var ac=HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click=function(){
    if(this.download&&/^blob:/.test(this.href)){var n=this.download;fetch(this.href).then(function(r){return r.text()}).then(function(t){return shareText(n,t,n)});return;}
    return ac.apply(this,arguments);
  };
  // Print: the app builds a srcdoc iframe and calls contentWindow.print() on load
  var ce=document.createElement.bind(document);
  document.createElement=function(tag){
    var el=ce.apply(document,arguments);
    if(String(tag).toLowerCase()==='iframe'){
      var h=null;
      Object.defineProperty(el,'onload',{configurable:true,get:function(){return h},set:function(fn){h=fn;
        el.addEventListener('load',function(){
          try{el.contentWindow.print=function(){var d=new Date().toISOString().slice(0,10);shareText('get-clarity-journal-'+d+'.html',el.srcdoc||el.contentDocument.documentElement.outerHTML,'Print or save your journal')};}catch(e){}
          try{fn.call(el)}catch(e){}
        },{once:true});
      }});
    }
    return el;
  };
})();
