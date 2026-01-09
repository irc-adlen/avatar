# Launch the project

All the project can be started with the [docker compose](./docker-compose.yml).
On the first launch, plenty of AI models will be downloaded. It might take a long time.

### Mic configuration

At first lauch, the stt shoul crash. In the logs you will find all the camera devices available.
You have to change the `INPUT_DEVICE` variable in the [voice recorder](./STT/voice_recorder.py) file.

### Camera configuration

A camera have to be plugged for the project to work.
