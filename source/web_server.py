from bottle import *
from pathlib import Path

import utils

app = Bottle()

@app.route("/")
def route__():
    redirect("/file/index.html")

@app.route("/file/<filepath:path>")
def route__file(filepath):
    return static_file(filepath, root = utils.get_project_dir() / "website" / "static")

host = input("Host: ")
port = input("Port: ")

app.run(host = host, port = port)
