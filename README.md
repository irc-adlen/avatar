# Launch the project

Everything is containerized with Docker.
To run the project, you must execute the [build_all.sh](./build_all.sh) script first. It will build all the necessary Docker images. (docker compose up --build could work as well, but it is not recommended).

Once the Dockers are built, the project can be started with the [docker compose](./docker-compose.yml).
On the first launch, plenty of AI models will be downloaded. It might take a long time.

You can refer to this [video]() to know which hardware is recommended to run the project.