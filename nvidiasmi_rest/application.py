import os

from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)


@app.route("/")
def hello_world():
    return "Hello Zihao!"


@app.route("/nvidia")
def smi():
    re = os.popen("nvidia-smi -q -x").read()
    return re


class Nvidia(Resource):
    def get(self):
        re = os.popen("nvidia-smi -q -x").readlines()
        return re


api.add_resource(Nvidia, "/nvidiasmi")
