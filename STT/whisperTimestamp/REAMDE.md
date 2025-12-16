# Install & Setup locally

### python venv

It is recomended to install this software in a python venv.
You can create one by doing this :
```bash
python3 -m venv venvName
source ./venvName/bin/activate
```

### pip dependencies

All the pip dependencies are in the `whisper-timestamp-requirements.txt` file.
To install them, you have to execute this :
```bash
pip install -r whisper-timestamp-requirements.txt
```

### start the project

```bash
python3 whisperTimestamp.py
```