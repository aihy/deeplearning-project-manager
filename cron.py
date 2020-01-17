from time import sleep

from monitor import begin_monit

if __name__ == "__main__":
    while True:
        try:
            begin_monit()
        except:
            pass
        sleep(60 * 5)
