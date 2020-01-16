import os
from time import time

import docker
from flask import Flask, request, jsonify
from flask_restful import Api
from notebook.auth import passwd

app = Flask(__name__)
api = Api(app)


@app.route("/")
def hello_world():
    return "Hello Zihao!"


@app.route("/nvidia")
def smi():
    re = os.popen("nvidia-smi -q -x").read()
    return re


def rop(command):
    return os.popen(command).read().strip()


@app.route("/delcontainer")
def delc():
    name = request.args.get("name")
    rop("docker stop " + name)
    rop("docker rm " + name)
    return "OK"


@app.route("/newcontainer")
def new():
    begin_time = time()
    path = request.args.get("path")
    image_id = request.args.get("image")
    jpasswd = request.args.get("jpasswd")
    cpasswd = request.args.get("cpasswd")
    user = request.args.get("user")

    rop("mkdir -p " + path)
    rop("chown " + user + ":" + user + " " + path)
    # add user to docker group
    rop("usermod -aG docker " + user)
    # docker run
    container_id = rop(
        "docker run -dit --gpus all -p 8888 -p 9999 -v " + path + ":/workspace " + image_id + " /bin/bash")
    uid = rop("id -u " + user)
    # 容器内新建用户
    rop(
        "docker exec " + container_id + " useradd -m -p \"$(openssl passwd -1 " + cpasswd + ")\" -s /bin/bash -u " + uid + " -U " + user)
    # 生成jupyter密码串
    j_passwd_sha1 = passwd(jpasswd)
    rop(
        "docker exec -d -u " + uid + ":" + uid + " " + container_id + " jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --LabApp.password=" + j_passwd_sha1)
    rop(
        "docker exec -d -u " + uid + ":" + uid + " " + container_id + " tensorboard --logdir=tensorboard_logs --port 9999 --bind_all")
    # 把用户加入容器内的sudo里
    rop("docker exec " + container_id + " usermod -aG sudo " + user)
    client = docker.from_env()
    ports = client.containers.get(container_id).ports
    name = client.containers.get(container_id).name
    j_port = ports['8888/tcp'][0]['HostPort']
    t_port = ports['9999/tcp'][0]['HostPort']
    end_time = time()
    re = {"uid": uid, "j_port": j_port, "t_port": t_port, "container_id": container_id, "name": name,
          "time": end_time - begin_time}
    return jsonify(re)
