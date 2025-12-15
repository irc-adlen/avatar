# Add new detecable person

To detect someone, the script needs two things :
- Add a picture of the person you want to recognize in the [faces](./python/faces/) folder.
- Before creating the postgres Docker for the first time, change the [init.sql](./postgres/init.sql) by adding your target informations. If the Docker has already been run, access it with pgAdmin add insert data in the *people* table.

# Install & Setup locally

### python venv

It is recomended to install this software in a python venv.
You can create one by doing this :
```bash
python3 -m venv venvName
source ./venvName/bin/activate
```

### pip dependencies

All the pip dependencies are in the `requirements.txt` file.
To install them, you have to execute this :
```bash
pip install -r requirements.txt
```

### check the code

Ruff helps to check the code integrity and unused imports.
```bash
ruff check ./firstTest.py
```

# Docker

All the project can be run using Docker.
It currently contains two Dockers.
Both can be run with the [docker compose](./docker-compose.yml)

### set up the env 

You have to rename the [.env-exemple](./.env-exemple) file to `.env`.
Then create your own variables.
```bash
mv .env-exemple .env
```

### run the Dockers

```bash
docker compose up
```

A window with your camera should pop displaying the camera and the pepeole that have been recognized.