import urllib.request
urls=['http://127.0.0.1:8000/static/particles/particle-styles.css','http://127.0.0.1:8000/static/particles/particle-terms.js','http://127.0.0.1:8000/static/particles/particle-system.js']
for u in urls:
    try:
        r=urllib.request.urlopen(u, timeout=5)
        print(u, r.status)
    except Exception as e:
        print(u, 'ERROR', type(e).__name__, e)
