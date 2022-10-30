#include <Arduino.h>

#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "model_data.h"

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
}

char buffer[7844];

void loop() {
  float image[28*28];
  int img_counter;

  if(Serial.available()){        
      Serial.readBytes(buffer, sizeof(buffer));
      int magic_number = (buffer[0] << 24) | (buffer[1] << 16) | (buffer[2] << 8) | buffer[3];

      Serial.println("Image block received");

      img_counter = 0;

      while (img_counter < 30) {
        int img_i = 0;
        for (int i = 4 + 28*28*img_counter; i < 4 + 28*28*(img_counter + 1); i++) {
          image[img_i - 4] = ((float) buffer[i]) / 255;
          img_i++;
        }

        input->data.f[0] = 1;
        for (int i = 1; i <= 28*28; i++) {
          input->data.f[i] = image[i - 1];   
        }

        int start = millis();

        TfLiteStatus invoke_status = interpreter->Invoke();

        if (invoke_status != kTfLiteOk) {
          TF_LITE_REPORT_ERROR(error_reporter, "Invoke failed on x: %f\n",
                              static_cast<double>(0.5));
          return;
        }

        int end = millis();

        // Serial.println("Image " + String(img_counter));
        // Serial.println("Execution time: " + String(end - start) + " milliseconds");

        int max_confidence = -10000000;
        int digit;

        for (int i = 0; i < 10; i++) {
          if (output->data.f[i] > max_confidence) {
            max_confidence = output->data.f[i];
            digit = i;
          }
        }
        // Serial.println("Digit: " + String(digit));

        Serial.println(String(img_counter) + ", " + String(end - start) + ", " + String(digit));

        img_counter++;
      }
    }
}