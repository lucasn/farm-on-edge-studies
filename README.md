# farm-on-edge-studies

This repository holds the code and material generated during my time on the project Farm on Edge.

### FederatedFogSimulation
This folder contains the simulation that was developed to evaluate the impact of the auction algorithm in the fog federation based on latency. The Latest version is the the 4th. The other versions contains experimental and incomplete code.

### SmartTrapSystem
This is the latest version of the embedded code to capture the images of the insects inside the trap to generate the database for the computer vision model. The system saves the images to an USB drive connected to the Raspberry Pi. If there's not an USB connected, the images are saved in the Raspberry storage and moved to the USB when connected.

### Auction Algorithms
This folder contains the implementations of the auction algorithm in Python.

### PiCameraServer
Those are the tests that have been made for study the Raspberry Pi Camera.

### Esp32MNIST
This is the embedded code for running a neural network on ESP32 to identify digits of the MNIST database. This was made to evaluate the suitability of the ESP32 for running neural networks models.

### ManipulateMNISTFiles
This is just some manipulations on the files of the MNIST database to facilitates the communication with the ESP32 when testing the neural networks.