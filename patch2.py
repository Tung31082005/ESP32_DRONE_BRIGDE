# -*- coding: utf-8 -*-
with open('frontend/video.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add pseudo-fullscreen CSS class
css_target = ".back-btn { background-color: #555; }"
css_replacement = ".back-btn { background-color: #555; }\n        .pseudo-fullscreen { position: fixed !important; top: 0; left: 0; width: 100vw !important; height: 100vh !important; z-index: 9999; background-color: black; margin: 0; padding: 0; max-width: 100%; max-height: 100%; display: flex !important; justify-content: center; align-items: center; }"
c = c.replace(css_target, css_replacement)

# 2. Fix JS Fullscreen logic
js_target = "document.getElementById('fsBtn').addEventListener('click', () => { const el = document.querySelector('.video-container'); if (document.fullscreenElement) { document.exitFullscreen(); } else { if(el.requestFullscreen) { el.requestFullscreen(); } else if (el.webkitRequestFullscreen) { el.webkitRequestFullscreen(); } } });"
js_replacement = "document.getElementById('fsBtn').addEventListener('click', () => { const el = document.querySelector('.video-container'); if (el.classList.contains('pseudo-fullscreen')) { el.classList.remove('pseudo-fullscreen'); document.body.style.overflow = 'auto'; } else { el.classList.add('pseudo-fullscreen'); document.body.style.overflow = 'hidden'; } });"
c = c.replace(js_target, js_replacement)

# 3. Change default resolution select to 160x120
c = c.replace('<option value="4">160x120 (Lowest)</option>', '<option value="4" selected>160x120 (Lowest)</option>')
c = c.replace('<option value="8" selected>640x480 (Normal)</option>', '<option value="8">640x480 (Normal)</option>')

with open('frontend/video.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
