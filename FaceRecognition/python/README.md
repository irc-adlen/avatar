# Install & Setup

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