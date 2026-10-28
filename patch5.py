# -*- coding: utf-8 -*-
with open('main/db_parameters.h', 'r', encoding='utf-8') as f:
    h = f.read()
h = h.replace('#define DB_PARAM_TOTAL_NUM          28', '#define DB_PARAM_TOTAL_NUM          29')
h = h.replace('extern db_parameter_t db_param_disable_console;', 'extern db_parameter_t db_param_disable_console;\nextern db_parameter_t db_param_disable_camera;')
h = h.replace('#define DB_PARAM_DISABLE_CONSOLE db_param_disable_console.value.db_param_u8.value', '#define DB_PARAM_DISABLE_CONSOLE db_param_disable_console.value.db_param_u8.value\n#define DB_PARAM_DISABLE_CAMERA db_param_disable_camera.value.db_param_u8.value')
with open('main/db_parameters.h', 'w', encoding='utf-8') as f:
    f.write(h)

with open('main/db_parameters.c', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('db_parameter_t db_param_disable_console = {\n        .db_name = "dis_console",\n        .type = UINT8,\n        .value = {.db_param_u8 = {.value = 0, .min = 0, .max = 1}}\n};', 'db_parameter_t db_param_disable_console = {\n        .db_name = "dis_console",\n        .type = UINT8,\n        .value = {.db_param_u8 = {.value = 0, .min = 0, .max = 1}}\n};\n\ndb_parameter_t db_param_disable_camera = {\n        .db_name = "disable_camera",\n        .type = UINT8,\n        .value = {.db_param_u8 = {.value = 0, .min = 0, .max = 1}}\n};')
c = c.replace('&db_param_disable_console\n    };', '&db_param_disable_console,\n            &db_param_disable_camera\n    };')
with open('main/db_parameters.c', 'w', encoding='utf-8') as f:
    f.write(c)

with open('main/camera_stream.c', 'r', encoding='utf-8') as f:
    cam = f.read()
cam = cam.replace('void start_camera_stream(void) {\n    cam_mutex = xSemaphoreCreateMutex();', 'void start_camera_stream(void) {\n    if (DB_PARAM_DISABLE_CAMERA) {\n        ESP_LOGI(TAG, "Camera module disabled by user in settings. Skipping stream server start.");\n        return;\n    }\n    cam_mutex = xSemaphoreCreateMutex();')
with open('main/camera_stream.c', 'w', encoding='utf-8') as f:
    f.write(cam)

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()
html_target = '''                  </div>
              </div>
              <div class="row" id="espnow_secret_div">'''
html_replacement = '''                  </div>
              </div>
              <div class="row">
                  <div class="twelve columns">
                      <label for="disable_camera">Disable Camera Module (Save Power & RAM, Requires Reboot)</label>
                      <select name="disable_camera" id="disable_camera">
                          <option value="0">Camera Enabled (Normal FPV)</option>
                          <option value="1">Camera Disabled (Telemetry Only NodeMCU Mode)</option>
                      </select>
                  </div>
              </div>
              <div class="row" id="espnow_secret_div">'''
html = html.replace(html_target, html_replacement)
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Done')
