from time import sleep

from monitor import begin_monit

if __name__ == "__main__":
    while True:
        begin_monit()
        sleep(60)
