#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "model_data.h"

#define OLED_SDA 4
#define OLED_SCL 15
#define OLED_RST 16
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RST);
namespace {
  tflite::ErrorReporter* error_reporter = nullptr;
  const tflite::Model* model = nullptr;
  tflite::MicroInterpreter* interpreter = nullptr;
  TfLiteTensor* input = nullptr;
  TfLiteTensor* output = nullptr;

  constexpr int kTensorArenaSize = 10 * 1024;
  uint8_t tensor_arena[kTensorArenaSize];

}

void setup() {
  Serial.begin(9600);
  while (!Serial);

  //reset OLED display via software
  pinMode(OLED_RST, OUTPUT);
  digitalWrite(OLED_RST, LOW);
  delay(20);
  digitalWrite(OLED_RST, HIGH);

  Wire.begin(OLED_SDA, OLED_SCL);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3c, false, false)) {
    Serial.println("Fail when starting up the display");
    while (true);
  }

  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0,0);
  display.clearDisplay();
  display.display();

  static tflite::MicroErrorReporter micro_error_reporter;
  error_reporter = &micro_error_reporter;

  model = tflite::GetModel(mnist_tflite);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    TF_LITE_REPORT_ERROR(error_reporter,
                         "Model provided is schema version %d not equal "
                         "to supported version %d.",
                         model->version(), TFLITE_SCHEMA_VERSION);
    return;
  }

  static tflite::AllOpsResolver resolver;

  static tflite::MicroInterpreter static_interpreter(
      model, resolver, tensor_arena, kTensorArenaSize, error_reporter);
  interpreter = &static_interpreter;

  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(error_reporter, "AllocateTensors() failed");
    return;
  }

  input = interpreter->input(0);
  output = interpreter->output(0);

  Serial.println("[X] Model information");
  Serial.println("Input type: " + String(input->type));
  Serial.println("Input type size: " + String(input->dims->size));
  Serial.println("First dimension: " + String(input->dims->data[0]));
  Serial.println("Second dimension: " + String(input->dims->data[1]));
  Serial.println("Third dimension: " + String(input->dims->data[2]));
  Serial.println("Quantization: " + String(input->quantization.type));
  Serial.println("Output type: " + String(output->type));
  Serial.println("Input type size: " + String(output->dims->size));
  Serial.println("First dimension: " + String(output->dims->data[0]));
  Serial.println("Second dimension: " + String(output->dims->data[1]));
}

char buffer[788];

void loop() {
  float image[28*28];

  if(Serial.available()){        
      Serial.readBytes(buffer, sizeof(buffer));
      int magic_number = (buffer[0] << 24) | (buffer[1] << 16) | (buffer[2] << 8) | buffer[3];
      for (int i = 4; i < 4 + 28*28; i++) {
        image[i - 4] = ((float) buffer[i]) / 255;
      }

      input->data.f[0] = 1;
      for (int i = 1; i <= 28*28; i++) {
        input->data.f[i] = image[i - 1];   
      }

      display.clearDisplay();
      display.setCursor(0,0);
      display.println("Running model...");
      display.display();

      int start = millis();

      TfLiteStatus invoke_status = interpreter->Invoke();

      if (invoke_status != kTfLiteOk) {
        TF_LITE_REPORT_ERROR(error_reporter, "Invoke failed on x: %f\n",
                            static_cast<double>(0.5));
        return;
      }

      int end = millis();

      display.println(String(end - start) + " milliseconds");

      Serial.println("Execution time: " + String(end - start) + " milliseconds");

      int max_confidence = -10000000;
      int digit;

      for (int i = 0; i < 10; i++) {
        if (output->data.f[i] > max_confidence) {
          max_confidence = output->data.f[i];
          digit = i;
        }
      }
      Serial.println("Digit: " + String(digit));
      display.println("Digit: " + String(digit));
      display.display();
    }
}