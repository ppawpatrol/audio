#include <WiFi.h>
#include <driver/i2s.h>

// Wi-Fi credentials
const char* ssid = "ssid";
const char* password = "password";

// I2S setup (same as your original code)
#define I2S_WS 25
#define I2S_SD 33
#define I2S_SCK 32
#define I2S_PORT I2S_NUM_0
#define bufferLen 64
int16_t sBuffer[bufferLen];

// TCP server setup
WiFiServer server(8080);  // TCP port to listen for connections

void i2s_install() {
  // Set up I2S Processor configuration
  const i2s_config_t i2s_config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 44100,
    .bits_per_sample = i2s_bits_per_sample_t(16),
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_STAND_I2S),
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = bufferLen,
    .use_apll = false
  };

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
}

void i2s_setpin() {
  // Set I2S pin configuration
  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = -1,
    .data_in_num = I2S_SD
  };

  i2s_set_pin(I2S_PORT, &pin_config);
}

void setup() {
  // Start Serial Monitor
  Serial.begin(115200);
  Serial.println("Connecting to WiFi...");

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());


  // Start TCP server
  server.begin();
  
  // Set up I2S for microphone
  i2s_install();
  i2s_setpin();
  i2s_start(I2S_PORT);
}

WiFiClient client;

void loop() {
  // Accept a new client if none is connected
  if (!client || !client.connected()) {
    client = server.available();
  //  Serial.println("New client connected");
  }

  // If client is connected, send audio
  if (client && client.connected()) {
    size_t bytesIn = 0;
    esp_err_t result = i2s_read(I2S_PORT, &sBuffer, bufferLen * sizeof(int16_t), &bytesIn, portMAX_DELAY);

    if (result == ESP_OK && bytesIn > 0) {
      client.write((uint8_t *)sBuffer, bytesIn);
    }
  }
}

