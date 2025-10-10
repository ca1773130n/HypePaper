class Registry:
    def __init__(self):
        self.action_registry = {}

    def register_action(self, name: str, cls: type):
        self.action_registry[name] = cls

    def get_action(self, name: str):
        return self.action_registry.get(name)

