class ActionTypes:
    SINGLE_TARGET = "single_target"
    ALL_TARGET = "all_target"

class Action:
    def __init__(self, owner):
        self.name = ""
        self.type = None
        self.owner = owner

    def do_action(self, targets):
        if targets is None:
            print(f"{self.name} has been passed None for targets")
            return 1

        if len(targets) != 1:
            print(f"{self.name} has been passed more than one target!!!!!")
            return 1
