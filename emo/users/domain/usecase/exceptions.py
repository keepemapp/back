class MissmatchPasswordException(Exception):
    def __init__(self, msg="Passwords do not match"):
        self.msg = msg
