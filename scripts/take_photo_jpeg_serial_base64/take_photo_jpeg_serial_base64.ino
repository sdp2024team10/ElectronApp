
// #include <Arduino.h>
#include "esp_camera.h"
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"
#include <base64.h>
#define REG_DEBUG_ON

void initCam() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  // config.xclk_freq_hz = 2000000;
  config.pixel_format = PIXFORMAT_JPEG;
  // config.pixel_format = PIXFORMAT_GRAYSCALE;
  config.frame_size = FRAMESIZE_QXGA;
  // config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 25;
  config.fb_count = 2;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  // config.fb_count = 1;
  // config.fb_location = CAMERA_FB_IN_DRAM;

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }

//   sensor_t *s = esp_camera_sensor_get();
  //initial sensors are flipped vertically and colors are a bit saturated
  //   if (s->id.PID == OV3660_PID) {
  //     s->set_vflip(s, 1);        //flip it back
  //     s->set_brightness(s, 1);   //up the blightness just a bit
  //     s->set_saturation(s, -2);  //lower the saturation
  //   }
  //   //drop down frame size for higher initial frame rate
  //   //s->set_framesize(s, FRAMESIZE_QVGA);
//   s->set_brightness(s, -10);                // -2 to 2
//   s->set_contrast(s, -1);                   // -2 to 2
//   s->set_saturation(s, 0);                  // -2 to 2
//   s->set_special_effect(s, 2);              // 0 to 6 (0 - No Effect, 1 - Negative, 2 - Grayscale, 3 - Red Tint, 4 - Green Tint, 5 - Blue Tint, 6 - Sepia)
//   s->set_whitebal(s, 1);                    // 0 = disable , 1 = enable
//   s->set_awb_gain(s, 1);                    // 0 = disable , 1 = enable
//   s->set_wb_mode(s, 3);                     // 0 to 4 - if awb_gain enabled (0 - Auto, 1 - Sunny, 2 - Cloudy, 3 - Office, 4 - Home)
//   s->set_exposure_ctrl(s, 1);               // 0 = disable , 1 = enable
//   s->set_aec2(s, 0);                        // 0 = disable , 1 = enable
//   s->set_ae_level(s, 2);                    // -2 to 2
//   s->set_aec_value(s, 1000);                // 0 to 1200
//   s->set_gain_ctrl(s, 1);                   // 0 = disable , 1 = enable
//   s->set_agc_gain(s, 30);                   // 0 to 30
//   s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
//   s->set_bpc(s, 0);                         // 0 = disable , 1 = enable
//   s->set_wpc(s, 1);                         // 0 = disable , 1 = enable
//   s->set_raw_gma(s, 1);                     // 0 = disable , 1 = enable
//   s->set_lenc(s, 1);                        // 0 = disable , 1 = enable
//   s->set_hmirror(s, 0);                     // 0 = disable , 1 = enable
//   s->set_vflip(s, 0);                       // 0 = disable , 1 = enable
//   s->set_dcw(s, 1);                         // 0 = disable , 1 = enable
//   s->set_colorbar(s, 0);                    // 0 = disable , 1 = enable

  // #if defined(CAMERA_MODEL_M5STACK_WIDE)
  //   s->set_vflip(s, 1);
  //   s->set_hmirror(s, 1);
  // #endif
}

void warmUpCamera() {
  // dark green tint goes away after you warm the camera up ... I guess
  camera_fb_t *frameBuffer = nullptr;
  for (int i = 0; i < 3; i++) {
    frameBuffer = esp_camera_fb_get();
    esp_camera_fb_return(frameBuffer);
    frameBuffer = nullptr;
  }
}

void takePictureAndSubmit() {
  warmUpCamera();
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed!");
    return;
  }

  //   Serial.print("{");
  //   Serial.print("\"width\":");
  //   Serial.print(fb->width);
  //   Serial.print(",");
  //   Serial.print("\"height\":");
  //   Serial.print(fb->height);
  //   Serial.print(",");
  //   Serial.print("\"image_jpeg_base64\":");
  Serial.print("\n");
  Serial.print("image_jpeg_base64:");
  //   Serial.print("\"");
  Serial.print(base64::encode(fb->buf, fb->len));
  Serial.print("\n");
  //   Serial.print("\"");
  //   Serial.print("}");

  // Killing cam resource
  esp_camera_fb_return(fb);
}

void setup() {
  //   pinMode(15, OUTPUT);
  //   digitalWrite(15, LOW);
  Serial.begin(460800);
  Serial.println("");
  Serial.println("hello, world!");
  initCam();
  takePictureAndSubmit();
  Serial.println("goodbye, world!");
}

void loop() {}
