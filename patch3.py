# -*- coding: utf-8 -*-
with open('main/camera_stream.c', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add current_framesize
c = c.replace('static volatile bool camera_should_run = true;\nstatic SemaphoreHandle_t cam_mutex;', 
              'static volatile bool camera_should_run = true;\nstatic SemaphoreHandle_t cam_mutex;\nstatic framesize_t current_framesize = FRAMESIZE_QQVGA;')

# 2. Update do_camera_init to use current_framesize
target_init = '''        sensor_t *s = esp_camera_sensor_get();
        if (s) {
            s->set_framesize(s, FRAMESIZE_QQVGA);
        }'''
replacement_init = '''        sensor_t *s = esp_camera_sensor_get();
        if (s) {
            s->set_framesize(s, current_framesize);
        }'''
c = c.replace(target_init, replacement_init)

# 3. Update resolution_handler
target_res = '''            int framesize = atoi(val + 4);
            sensor_t *s = esp_camera_sensor_get();
            if (s) {
                s->set_framesize(s, (framesize_t)framesize);
            }'''
replacement_res = '''            int framesize = atoi(val + 4);
            xSemaphoreTake(cam_mutex, portMAX_DELAY);
            current_framesize = (framesize_t)framesize;
            if (camera_initialized) {
                sensor_t *s = esp_camera_sensor_get();
                if (s) {
                    s->set_framesize(s, current_framesize);
                }
            }
            xSemaphoreGive(cam_mutex);'''
c = c.replace(target_res, replacement_res)

with open('main/camera_stream.c', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
