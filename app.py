from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from requests import get

app = Flask(__name__)
app.secret_key = b"\x9b8'\x18\x9c4E\xad\x1b\x84\x0fh\xa5\x17f\x1c"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:2355@127.0.0.1/wzh'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)


@app.route("/")
def index():
    if "username" in session:
        servers = Server.query.all()
        server_ips = []
        for server in servers:
            server_ips.append([server.serverIp, server.gpuAmount])
        return render_template("index.html", username=session.get("username"), servers=server_ips)
    else:
        return render_template("index.html", notlogin=1)

@app.route("/usekey")
def usekey():
    return reder_template("usekey.html")


@app.route("/getmonitordata")
def gmd():
    ip = request.args.get("ip")
    gpu_amount = Server.query.filter_by(serverIp=ip).first().gpuAmount
    lgd = []
    for i in range(gpu_amount):
        lgd.append("GPU" + str(i))
        lgd.append("")
    time_all = GpuMonitor.query.filter(GpuMonitor.serverIp == ip, GpuMonitor.gpuNumber == 0,
                                       GpuMonitor.gmtCreate > (datetime.now() + timedelta(days=-1)).strftime(
                                           "%Y-%m-%d %H:%M:%S")).all()
    x = []
    for time in time_all:
        x.append(time.gmtCreate)
    y = {"xl": x, "lgd": lgd}
    for i in range(gpu_amount):
        gpu_all = GpuMonitor.query.filter(GpuMonitor.serverIp == ip, GpuMonitor.gpuNumber == 0,
                                          GpuMonitor.gmtCreate > (datetime.now() + timedelta(days=-1)).strftime(
                                              "%Y-%m-%d %H:%M:%S")).all()
        y1 = []
        y2 = []
        for moni in gpu_all:
            y1.append(moni.usageUsed)
            y2.append(moni.usageFree)
        y["y" + str(i) + "y1"] = y1
        y["y" + str(i) + "y2"] = y2
    return jsonify(y)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        passwd = request.form["password"]
        user = User.query.filter_by(username=name, password=passwd).first()
        if user is None:
            return render_template("login.html", error="您输入的用户名或密码有误！忘记密码请微信联系王子豪！", notlogin=1)
        else:
            session["username"] = name
            return redirect(url_for("index"))
    else:
        return render_template("login.html", notlogin=1)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        name = request.form["username"]
        passwd = request.form["password"]
        passwd_agn = request.form["password_again"]
        name_in_server = request.form["nameinserver"]
        if passwd != passwd_agn:
            return render_template("signin.html", error="您两次输入的密码不一致！", notlogin=1)
        # TODO 把密码一致检测放到js里面
        # 先检查name是否在UserControl表中，UserControl表中的用户才允许注册
        user_control = UserControl.query.filter_by(username=name).first()
        if user_control is None:
            return render_template("signin.html", error="您不在可注册范围内，请微信联系王子豪！", notlogin=1)
        # 再检查要注册的姓名是否已经注册了
        user = User.query.filter_by(username=name).first()
        if user is None:
            db.session.add(User(username=name, password=passwd, userInServer=name_in_server))
            db.session.commit()
            session["username"] = name
            return redirect(url_for("index"))
        else:
            return render_template("signin.html", error2=1, notlogin=1)
        # TODO 加入google authenticator
    else:
        return render_template("signin.html", notlogin=1)


# TODO 加入添加服务器页面

@app.route("/logout")
def logout():
    session.pop("username")
    return redirect(url_for("index"))


@app.route("/new", methods=["GET", "POST"])
def new():
    if "username" not in session:
        return redirect(url_for("login"))
    else:
        name = session.get("username")
        nameinserver = User.query.filter_by(username=name).first().userInServer
        if request.method == "POST":
            server_ip = request.form.get("server")
            path = request.form.get("path")
            if path == '/':
                render_template("new.html", username=name, nameinserver=nameinserver)
            image_version = request.form["version"]
            if image_version == "PyTorch1.3-cuda10.1-cudnn7":
                image = "wzh-pytorch:1"
            elif image_version == "PyTorch0.4.1-cuda9-cudnn7":
                image = "wzh-pytorch:0"
            elif image_version == "Tensorflow2.1.0-cuda10.1":
                image = "wzh-tensorflow:2"
            else:
                raise RuntimeError(image_version)
            port = Port.query.filter_by(type="flask", serverIp=server_ip).first().port
            r = get("http://127.0.0.1:" + str(port) + "/newcontainer",
                    {"path": path, "image": image, "jpasswd": "6666", "cpasswd": "8888", "user": nameinserver})
            d = r.json()
            c = Container(imageVersion=image_version, serverIp=server_ip, image=image, username=name, path=path,
                          containerId=d["container_id"], containerName=d["name"], userInServer=nameinserver,
                          uid=d["uid"], createTime=d["time"], jport=d["j_port"], tport=d["t_port"])
            db.session.add(c)
            db.session.commit()
            return render_template("success.html", username=name, time=d["time"])
        else:
            return render_template("new.html", username=name, nameinserver=nameinserver)


@app.route("/my")
def my():
    if "username" not in session:
        return redirect(url_for("login"))
    else:
        name = session.get("username")
        all_container = Container.query.filter_by(username=name).all()
        return render_template("my.html", username=name, ac=all_container)


@app.route("/delete")
def del_container():
    if "username" not in session:
        return redirect(url_for("login"))
    else:
        cname = request.args.get("name")
        name = session.get("username")
        container = Container.query.filter_by(username=name, containerName=cname).first_or_404()
        if container:
            server_ip = container.serverIp
            port = Port.query.filter_by(type="flask", serverIp=server_ip).first().port
            r = get("http://127.0.0.1:" + str(port) + "/delcontainer", {"name": cname})
            if r.text == "OK":
                db.session.delete(container)
                db.session.commit()
                return redirect(url_for("my"))
            else:
                return "Error"
        else:
            return render_template("index.html", username=container)


class Container(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmtCreate = db.Column(db.DateTime, default=datetime.now)
    gmtModified = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    serverIp = db.Column(db.String(80), unique=False, nullable=False)  # 服务器ip地址
    containerId = db.Column(db.String(128), unique=True, nullable=False)
    containerName = db.Column(db.String(64), unique=True, nullable=False)
    path = db.Column(db.String(64), nullable=False)
    imageVersion = db.Column(db.String(64), nullable=False)
    image = db.Column(db.String(64), nullable=False)
    userInServer = db.Column(db.String(80), unique=False, nullable=False)
    uid = db.Column(db.Integer, unique=False, nullable=False)
    createTime = db.Column(db.Float)
    jport = db.Column(db.Integer)
    tport = db.Column(db.Integer)
    username = db.Column(db.String(80), unique=False, nullable=False)

    def __repr__(self):
        return '<Container Name %r>' % self.containerName


# 用户表，包含姓名和密码
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmtCreate = db.Column(db.DateTime, default=datetime.now)
    gmtModified = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)
    userInServer = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


# 用户控制表，只有此表中的用户才允许注册
class UserControl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmtCreate = db.Column(db.DateTime, default=datetime.now)
    gmtModified = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<UserControl %r>' % self.username


# gpu监控表 记录gpu监控数据
class GpuMonitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmtCreate = db.Column(db.DateTime, default=datetime.now)
    gmtModified = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    serverIp = db.Column(db.String(80), unique=False, nullable=False)  # 服务器ip地址
    gpuNumber = db.Column(db.Integer, unique=False, nullable=False)  # gpu序号
    productName = db.Column(db.String(32), unique=False, nullable=False)  # gpu型号
    fanSpeed = db.Column(db.Integer, unique=False, nullable=False)  # 风扇转速0-100
    usageTotal = db.Column(db.Integer, unique=False, nullable=False)  # 显存total
    usageUsed = db.Column(db.Integer, unique=False, nullable=False)  # 显存used
    usageFree = db.Column(db.Integer, unique=False, nullable=False)  # 显存free
    gpuUtil = db.Column(db.Integer, unique=False, nullable=False)  # 显卡使用率
    gpuTemp = db.Column(db.Integer, unique=False, nullable=False)  # 温度

    def __repr__(self):
        return '<GpuMonitor %r Gpu %r>' % (self.serverIp, self.gpuNumber)


# 端口映射表 记录服务器端口映射情况
class Port(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmtCreate = db.Column(db.DateTime, default=datetime.now)
    gmtModified = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    serverIp = db.Column(db.String(80), unique=False, nullable=False)  # 服务器ip地址
    type = db.Column(db.String(32), unique=False, nullable=False)  # 端口用途 shell,jupyter,tensorboard
    port = db.Column(db.Integer, unique=False, nullable=False)  # 端口号

    def __repr__(self):
        return '<serverIp %r type %r port %r>' % (self.serverIp, self.type, self.port)


# 服务器表
class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmtCreate = db.Column(db.DateTime, default=datetime.now)
    gmtModified = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    serverIp = db.Column(db.String(80), unique=True, nullable=False)  # 服务器ip地址
    rootPassword = db.Column(db.String(80), unique=False, nullable=True)  # 服务器ip地址
    gpuAmount = db.Column(db.Integer, unique=False, nullable=True)  # gpu数量

    def __repr__(self):
        return '<serverIp %r gpuAmount %r>' % (self.serverIp, self.gpuAmount)


if __name__ == '__main__':
    app.run()
