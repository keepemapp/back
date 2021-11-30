class MissmatchPasswordException(Exception):
    def __init__(self, msg="Passwords do not match"):
        self.msg = msg


class EmailAlreadyExistsException(Exception):
    def __init__(self, msg="Email already exists"):
        self.msg = msg


class UsernameAlreadyExistsException(Exception):
    def __init__(self, msg="Username already exists"):
        self.msg = msg
