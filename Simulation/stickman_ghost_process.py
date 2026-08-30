import setproctitle, sys, time

setproctitle.setproctitle(sys.argv[1])

while True:
    time.sleep(1)