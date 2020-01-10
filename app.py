from datetime import datetime

from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

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


@app.route("/getmonitordata")
def gmd():
    ip = request.args.get("ip")
    gpu_amount = Server.query.filter_by(serverIp=ip).first().gpuAmount
    lgd = []
    for i in range(gpu_amount):
        lgd.append("GPU" + str(i))
        lgd.append("")
    time_all = GpuMonitor.query.filter_by(serverIp=ip, gpuNumber=0).all()
    x = []
    for time in time_all:
        x.append(time.gmtCreate)
    y = {"xl": x, "lgd": lgd}
    for i in range(gpu_amount):
        gpu_all = GpuMonitor.query.filter_by(serverIp=ip, gpuNumber=i).all()
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
        if passwd != passwd_agn:
            return render_template("signin.html", error="您两次输入的密码不一致！", notlogin=1)
        # 先检查name是否在UserControl表中，UserControl表中的用户才允许注册
        user_control = UserControl.query.filter_by(username=name).first()
        if user_control is None:
            return render_template("signin.html", error="您不在可注册范围内，请微信联系王子豪！", notlogin=1)
        # 再检查要注册的姓名是否已经注册了
        user = User.query.filter_by(username=name).first()
        if user is None:
            db.session.add(User(username=name, password=passwd))
            db.session.commit()
            session["username"] = name
            return redirect(url_for("index"))
        else:
            return render_template("signin.html", login=1)
    else:
        return render_template("signin.html", notlogin=1)


@app.route("/logout")
def logout():
    session.pop("username")
    return redirect(url_for("index"))


# 用户表，包含姓名和密码
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmtCreate = db.Column(db.DateTime, default=datetime.now)
    gmtModified = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)

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
