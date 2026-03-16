# MyProject

MyProject is a client/server Python module with CLI and admin commands, using Flask + Waitress.

## 1. Installation in a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
cd /path/to/scanctrl
pip install .
```

# User-level install
```bash
python -m setup_completion
```

# Or system-wide (requires root)
```bash
sudo python -m setup_completion
```
# Running commands

## Start server
```bash
sudo myproject-admin server start
```
# Run client command
```bash
myproject status
myproject debug
```
# Adding a new command

## 1. Add a task function
In /src/myproject/server.py, add a task function
```python
def new_task(...):
    ...
```
## 2. Add the Flask endpoint
Add the Flask endpoint in /src/myproject/server.py
```python
@app.route("/new-task", methods=["POST"])
def new_task():
    ...
```

## 3. Add a client method
In /src/myproject/client.py, add a client method
```python
def new_task(self, ...):
    ...
```

## 4. Add a CLI command
Finally add the command in the CLI (command line interface), in /src/myproject/cli.py,
```python
@cli.command()
def new_task(...):
    ...
```


