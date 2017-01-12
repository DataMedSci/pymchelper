class ExecutorError(Exception):
    pass


class ProcessAlreadyStarted(Exception):
    def __init__(self):
        self.value = "Process has been already started"
