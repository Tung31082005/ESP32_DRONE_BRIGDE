# -*- coding: utf-8 -*-
import re
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = r'(<select name="dis_console" id="dis_console">.*?</select>\s*</div>\s*</div>)'
replacement = r'\1\n              <div class="row">\n                  <div class="twelve columns">\n                      <label for="disable_camera">Disable Camera Module (Save Power & RAM, Requires Reboot)</label>\n                      <select name="disable_camera" id="disable_camera">\n                          <option value="0">Camera Enabled (Normal FPV)</option>\n                          <option value="1">Camera Disabled (Telemetry Only NodeMCU Mode)</option>\n                      </select>\n                  </div>\n              </div>'

html = re.sub(target, replacement, html, flags=re.DOTALL)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Done")
