# STT & Mqtt broker

This folder contains the [docker-compose](./docker-compose.yml) that launches the STT when a mqtt message is recieved on the topic *stt/start*.

## Start the docker compose

#### Requirements

A GPU has to work on the host.

```bash
nvidia-smi
```

Install NVIDIA Container toolkit

```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

#### Build & start

The first time you start it, you have to build the [Dockerfile](./Dockerfile).
```bash
docker compose up --build
```

## Test it

#### mqtt message

The voice detector triggers after a message on the topic *stt/start*.
You can send one manually to test
```bash
mosquitto_pub -h localhost -t stt/start -m "go"
```
#### configure the mic
When the voice detector is triggered, all the mics are displayed.
You can change which one you want by modifiying the following file in the [voice_recorder](./voice_recorder.py) file. 
```py
INPUT_DEVICE = the_id_of_your_device
```

