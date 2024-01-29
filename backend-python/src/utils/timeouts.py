import threading

class Timeout:
    def __init__(self, callback, delay):
        self.callback = callback
        self.timer = threading.Timer(delay / 1000, self._on_timeout)

    def start(self):
        self.timer.start()

    def _on_timeout(self):
        self.callback()

    def cancel(self):
        self.timer.cancel()

timeouts = {}

def setTimeout(callback, delay):
    timer = Timeout(callback, delay)
    timer.start()
    timeouts[id(timer)] = timer
    return id(timer)

def clearTimeout(timer_id):
    if timer_id in timeouts:
        timer = timeouts[timer_id]
        timer.cancel()
        del timeouts[timer_id]