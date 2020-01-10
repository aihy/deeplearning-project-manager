import os
import random
from time import sleep

from requests import get

from app import Port, db


# 对ip port发送hello，检查tunnel是否完好，完好返回true，否则返回false
def say_hello(port):
    if port is None:
        return False
    try:
        h1 = get("http://127.0.0.1:" + str(port) + "/").text
        if h1 == "Hello Zihao!":
            print("tunnel 建立成功")
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def start_tunnel(ip, typet):
    # 先查ip type对应端口
    # 1 如果没找到
    # 2 如果找到了
    #      看看行不行，不行就重新new
    query_port = Port.query.filter_by(serverIp=ip, type=typet).first()
    if query_port is None:
        print("请先new_tunnel")
        raise RuntimeError
    else:
        port = query_port.port
    retry_times = 0
    while True:
        if say_hello(port):
            break
        else:
            if retry_times > 100:
                print("ssh tunnel 建立失败")
                raise RuntimeError
            sleep(1)
            retry_times += 1
            os.system("ssh -4 -p 5102 zihao_wang@" + ip + " -L " + str(port) + ":127.0.0.1:" + str(port) + " -N &")
    return port


def new_tunnel(ip, typet, port=None):
    if port is None:
        port = random.randint(11000, 65500)
    query_port = Port.query.filter_by(serverIp=ip, type=typet).first()
    if query_port is None:
        add_port = Port(serverIp=ip, type=typet, port=port)
        db.session.add(add_port)
    else:
        query_port.port = port
    db.session.commit()
    return port


if __name__ == "__main__":
    # print(new_tunnel("183.174.228.96", "flask", 11000))
    # print(say_hello(13124))
    print(start_tunnel("183.174.228.86", "flask"))
