# Native fix: root index.html becomes the app shell itself (the native asset servers
# fall back to /index.html for extension-less paths like /app/, so a redirect to /app/ loops).
import sys
www=sys.argv[1]
h=open(f'{www}/app/index.html').read()
inj='<script>if(location.pathname==="/"||location.pathname==="/index.html")history.replaceState(null,"","/app/")</script>'
h=h.replace('<head>','<head>'+inj,1)
open(f'{www}/index.html','w').write(h)
print('root index.html replaced with app shell, %d bytes'%len(h))
