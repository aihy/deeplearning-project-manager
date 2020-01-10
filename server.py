from app import Server, db


def new_server(ip):
    new = Server(serverIp=ip)
    db.session.add(new)
    db.session.commit()
