# -*- coding: utf-8 -*-
with open('frontend/video.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('<button class="back-btn" onclick="window.location.href=\'/\'">Back</button>', '<button class="back-btn" onclick="window.location.href=\'/\'">Back</button>\n        <button id="fsBtn" style="background-color: #9c27b0;">Fullscreen</button>')
with open('frontend/video.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
