class ExecutorError(Exception):
    pass

class NotEnoughMemoryError(Exception):
    def __init__(self):
        self.value = "Not enough RAM memory to run shield-hit"

class ProcessAlreadyStarted(Exception):
    def __init__(self):
        self.value = "Process has been already started"