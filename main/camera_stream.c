#include "camera_stream.h"
#include "esp_camera.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "db_parameters.h"
#include "driver/gpio.h"
#include "esp_wifi.h"
#include "globals.h"

#define CAM_PIN_PWDN    32
#define CAM_PIN_RESET   -1
#define CAM_PIN_XCLK    0
#define CAM_PIN_SIOD    26
#define CAM_PIN_SIOC    27
#define CAM_PIN_D7      35
#define CAM_PIN_D6      34
#define CAM_PIN_D5      39
#define CAM_PIN_D4      36
#define CAM_PIN_D3      21
#define CAM_PIN_D2      19
#define CAM_PIN_D1      18
#define CAM_PIN_D0       5
#define CAM_PIN_VSYNC   25
#define CAM_PIN_HREF    23
#define CAM_PIN_PCLK    22
#define FLASH_LED_PIN    4

static const char *TAG = "cam_stream";
static httpd_handle_t stream_httpd = NULL;

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

static bool camera_initialized = false;
static int active_streams = 0;
static volatile bool camera_should_run = true;
static SemaphoreHandle_t cam_mutex;
static framesize_t current_framesize = FRAMESIZE_CIF;

static esp_err_t do_camera_init(void) {
    if (camera_initialized) return ESP_OK;

    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = CAM_PIN_D0;
    config.pin_d1 = CAM_PIN_D1;
    config.pin_d2 = CAM_PIN_D2;
    config.pin_d3 = CAM_PIN_D3;
    config.pin_d4 = CAM_PIN_D4;
    config.pin_d5 = CAM_PIN_D5;
    config.pin_d6 = CAM_PIN_D6;
    config.pin_d7 = CAM_PIN_D7;
    config.pin_xclk = CAM_PIN_XCLK;
    config.pin_pclk = CAM_PIN_PCLK;
    config.pin_vsync = CAM_PIN_VSYNC;
    config.pin_href = CAM_PIN_HREF;
    config.pin_sccb_sda = CAM_PIN_SIOD;
    config.pin_sccb_scl = CAM_PIN_SIOC;
    config.pin_pwdn = CAM_PIN_PWDN;
    config.pin_reset = CAM_PIN_RESET;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = current_framesize;
    config.jpeg_quality = 10;
    config.fb_count = 2;

    gpio_set_level(CAM_PIN_PWDN, 0); // Power on sensor
    vTaskDelay(pdMS_TO_TICKS(100));  // Wait for sensor to wake up

    esp_err_t err = esp_camera_init(&config);
    if (err == ESP_OK) {
        camera_initialized = true;
        ESP_LOGI(TAG, "Camera initialized successfully");
        sensor_t *s = esp_camera_sensor_get();
        if (s) {
            s->set_framesize(s, current_framesize);
            s->set_special_effect(s, 2); // 2 = Grayscale. This significantly reduces JPEG size and Wi-Fi load.
        }
    } else {
        ESP_LOGE(TAG, "Camera init failed: 0x%x", err);
        gpio_set_level(CAM_PIN_PWDN, 1); // Power off if failed
    }
    return err;
}

// ---------- Stream handler ----------

static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len = 0;
    uint8_t *_jpg_buf = NULL;
    char part_buf[64];

    // 1. FAIL-SAFE: Kill any abandoned "ghost" streams from page reloads
    // Mutex protects the entire stream replacement sequence to prevent two
    // concurrent handlers from racing through the kill-wait-init cycle.
    xSemaphoreTake(cam_mutex, portMAX_DELAY);
    camera_should_run = false;
    xSemaphoreGive(cam_mutex);

    int wait_cycles = 0;
    while (active_streams > 0 && wait_cycles < 20) { // Wait max 2 seconds for old stream to die
        vTaskDelay(pdMS_TO_TICKS(100));
        wait_cycles++;
    }

    xSemaphoreTake(cam_mutex, portMAX_DELAY);
    camera_should_run = true;
    if (active_streams == 0) {
        do_camera_init();
    }
    active_streams++;
    xSemaphoreGive(cam_mutex);

    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if (res != ESP_OK) goto stream_exit;
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

    while (camera_should_run) {
        if (!camera_initialized) {
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }

        fb = esp_camera_fb_get();
        if (!fb) {
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }

        _jpg_buf_len = fb->len;
        _jpg_buf = fb->buf;

        if (res == ESP_OK)
            res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
        if (res == ESP_OK) {
            size_t hlen = snprintf(part_buf, sizeof(part_buf), _STREAM_PART, _jpg_buf_len);
            res = httpd_resp_send_chunk(req, part_buf, hlen);
        }
        if (res == ESP_OK)
            res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);

        esp_camera_fb_return(fb);
        fb = NULL;
        _jpg_buf = NULL;

        if (res != ESP_OK) break;

        // Track bandwidth stats globally
        db_total_bytes_sent += _jpg_buf_len;
        db_total_frames_sent++;
        db_last_frame_size = _jpg_buf_len;

        // Cap FPS to ~15fps (Requested by user to save bandwidth for long range)
        vTaskDelay(pdMS_TO_TICKS(66));
    }

stream_exit:
    xSemaphoreTake(cam_mutex, portMAX_DELAY);
    active_streams--;
    xSemaphoreGive(cam_mutex);

    return res;
}

// ---------- Flash LED handler ----------

static esp_err_t light_handler(httpd_req_t *req) {
    char buf[10];
    if (httpd_req_get_url_query_str(req, buf, sizeof(buf)) == ESP_OK) {
        if (strstr(buf, "val=1")) {
            gpio_set_direction(FLASH_LED_PIN, GPIO_MODE_OUTPUT);
            gpio_set_level(FLASH_LED_PIN, 1);
        } else {
            gpio_set_level(FLASH_LED_PIN, 0);
        }
    }
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, "OK", HTTPD_RESP_USE_STRLEN);
}

// ---------- Resolution handler ----------

static esp_err_t resolution_handler(httpd_req_t *req) {
    char buf[20];
    if (httpd_req_get_url_query_str(req, buf, sizeof(buf)) == ESP_OK) {
        char *val = strstr(buf, "val=");
        if (val) {
            int framesize = atoi(val + 4);
            xSemaphoreTake(cam_mutex, portMAX_DELAY);
            current_framesize = (framesize_t)framesize;
            if (camera_initialized) {
                sensor_t *s = esp_camera_sensor_get();
                if (s) {
                    s->set_framesize(s, current_framesize);
                }
            }
            xSemaphoreGive(cam_mutex);
        }
    }
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, "OK", HTTPD_RESP_USE_STRLEN);
}

// ---------- RSSI handler ----------

static esp_err_t rssi_handler(httpd_req_t *req) {
    char resp[32] = "{\"rssi\": 0}";
    wifi_ap_record_t ap_info;
    wifi_sta_list_t sta_list;

    if (esp_wifi_sta_get_ap_info(&ap_info) == ESP_OK) {
        snprintf(resp, sizeof(resp), "{\"rssi\": %d}", ap_info.rssi);
    } else if (esp_wifi_ap_get_sta_list(&sta_list) == ESP_OK && sta_list.num > 0) {
        snprintf(resp, sizeof(resp), "{\"rssi\": %d}", sta_list.sta[0].rssi);
    }

    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, resp, HTTPD_RESP_USE_STRLEN);
}

// ---------- Stream stats handler (bandwidth monitoring) ----------

static esp_err_t stats_handler(httpd_req_t *req) {
    char resp[128];
    snprintf(resp, sizeof(resp),
             "{\"bytes\":%lu,\"frames\":%lu,\"last_size\":%lu}",
             (unsigned long)db_total_bytes_sent,
             (unsigned long)db_total_frames_sent,
             (unsigned long)db_last_frame_size);
    // Reset counters after each read so frontend can compute per-second rates
    db_total_bytes_sent = 0;
    db_total_frames_sent = 0;

    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, resp, HTTPD_RESP_USE_STRLEN);
}

// ---------- Dummy camera power handler (legacy compatibility) ----------
// The actual init/deinit is now safely managed by stream_handler tracking active clients.
static esp_err_t power_handler(httpd_req_t *req) {
    char buf[16];
    char resp[48] = "{\"camera\": \"unknown\"}";

    if (httpd_req_get_url_query_str(req, buf, sizeof(buf)) == ESP_OK) {
        if (strstr(buf, "state=1") != NULL) {
            camera_should_run = true;
            snprintf(resp, sizeof(resp), "{\"camera\": \"on\"}");
        } else if (strstr(buf, "state=0") != NULL) {
            camera_should_run = false;
            snprintf(resp, sizeof(resp), "{\"camera\": \"off\"}");
        }
    }

    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, resp, HTTPD_RESP_USE_STRLEN);
}

// ---------- Entry point ----------

void start_camera_stream(void) {
    if (DB_PARAM_DISABLE_CAMERA) {
        ESP_LOGI(TAG, "Camera module disabled by user in settings. Skipping stream server start.");
        return;
    }
    cam_mutex = xSemaphoreCreateMutex();

    // In ESP-NOW LR mode: hard-kill camera power and skip all HTTP servers
    if (DB_PARAM_RADIO_MODE == DB_WIFI_MODE_ESPNOW_AIR || DB_PARAM_RADIO_MODE == DB_WIFI_MODE_ESPNOW_GND) {
        ESP_LOGI(TAG, "LR Mode detected. Disabling camera hardware to save power and bandwidth.");
        gpio_reset_pin(CAM_PIN_PWDN);
        gpio_set_direction(CAM_PIN_PWDN, GPIO_MODE_OUTPUT);
        gpio_set_level(CAM_PIN_PWDN, 1);
        return;
    }

    // Setup GPIO for Flash LED and Camera PWDN
    gpio_reset_pin(FLASH_LED_PIN);
    gpio_set_direction(FLASH_LED_PIN, GPIO_MODE_OUTPUT);
    gpio_set_level(FLASH_LED_PIN, 0);

    gpio_reset_pin(CAM_PIN_PWDN);
    gpio_set_direction(CAM_PIN_PWDN, GPIO_MODE_OUTPUT);
    gpio_set_level(CAM_PIN_PWDN, 1);  // Camera OFF at boot to save power

    // Start stream server on port 81
    httpd_config_t httpd_config = HTTPD_DEFAULT_CONFIG();
    httpd_config.server_port = 81;
    httpd_config.ctrl_port = 32769;
    httpd_config.core_id = 1;

    httpd_uri_t stream_uri = { .uri = "/stream", .method = HTTP_GET, .handler = stream_handler, .user_ctx = NULL };

    ESP_LOGI(TAG, "Starting stream server on port: '%d'", httpd_config.server_port);
    if (httpd_start(&stream_httpd, &httpd_config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
    }

    // Start control server on port 82 (separate from stream on port 81)
    httpd_handle_t ctrl_httpd = NULL;
    httpd_config_t ctrl_config = HTTPD_DEFAULT_CONFIG();
    ctrl_config.server_port = 82;
    ctrl_config.ctrl_port = 32770;
    ctrl_config.core_id = 1;

    httpd_uri_t light_uri = { .uri = "/light", .method = HTTP_GET, .handler = light_handler, .user_ctx = NULL };
    httpd_uri_t res_uri = { .uri = "/resolution", .method = HTTP_GET, .handler = resolution_handler, .user_ctx = NULL };
    httpd_uri_t rssi_uri = { .uri = "/rssi", .method = HTTP_GET, .handler = rssi_handler, .user_ctx = NULL };
    httpd_uri_t power_uri = { .uri = "/cam_power", .method = HTTP_GET, .handler = power_handler, .user_ctx = NULL };
    httpd_uri_t stats_uri = { .uri = "/stats", .method = HTTP_GET, .handler = stats_handler, .user_ctx = NULL };

    ESP_LOGI(TAG, "Starting control server on port: '%d'", ctrl_config.server_port);
    if (httpd_start(&ctrl_httpd, &ctrl_config) == ESP_OK) {
        httpd_register_uri_handler(ctrl_httpd, &light_uri);
        httpd_register_uri_handler(ctrl_httpd, &res_uri);
        httpd_register_uri_handler(ctrl_httpd, &rssi_uri);
        httpd_register_uri_handler(ctrl_httpd, &power_uri);
        httpd_register_uri_handler(ctrl_httpd, &stats_uri);
    }
}




