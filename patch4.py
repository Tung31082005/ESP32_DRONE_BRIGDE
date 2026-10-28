# -*- coding: utf-8 -*-
with open('main/camera_stream.c', 'r', encoding='utf-8') as f:
    c = f.read()

target_stream = '''    xSemaphoreTake(cam_mutex, portMAX_DELAY);
    if (active_streams == 0) {
        do_camera_init();
    }
    active_streams++;
    xSemaphoreGive(cam_mutex);'''

replacement_stream = '''    // 1. FAIL-SAFE: Kill any abandoned "ghost" streams from page reloads
    camera_should_run = false;
    int wait_cycles = 0;
    while (active_streams > 0 && wait_cycles < 20) { // Wait max 2 seconds for old stream to die
        vTaskDelay(pdMS_TO_TICKS(100));
        wait_cycles++;
    }
    
    camera_should_run = true;
    xSemaphoreTake(cam_mutex, portMAX_DELAY);
    if (active_streams == 0) {
        do_camera_init();
    }
    active_streams++;
    xSemaphoreGive(cam_mutex);'''

c = c.replace(target_stream, replacement_stream)

# Enable TWDT Panic in sdkconfig
with open('sdkconfig', 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('# CONFIG_ESP_TASK_WDT_PANIC is not set', 'CONFIG_ESP_TASK_WDT_PANIC=y')

with open('main/camera_stream.c', 'w', encoding='utf-8') as f:
    f.write(c)
with open('sdkconfig', 'w', encoding='utf-8') as f:
    f.write(s)
print('Done')
