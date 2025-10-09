import subprocess

from sotapapers.core.registry import Registry

from enum import Enum

registry = Registry()

class ActionMeta(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        new_class = super().__new__(cls, name, bases, attrs)
        action_type = attrs.get('action_type')
        if action_type:
            registry.register_action(action_type, new_class)
        return new_class

class ActionType(Enum):
    READ_FILE = 'Reading file'
    EXECUTE_SHELL_COMMAND = 'Executing shell command'

class ActionInput:
    def __init__(self, prompt: str, files: list[str] = None):
        self.prompt = prompt
        self.files = files

class ActionOutput:
    def __init__(self, success: bool, message: str, files: list[str] = None):
        self.success = success
        self.message = message
        self.files = files
       
class Performer:
    def perform_action(self, action_type: ActionType, input: ActionInput) -> ActionOutput:
        raise NotImplementedError('Perform action method should be implemented by subclasses')

    def show_log(self, message: str, level: str = 'INFO'):
        raise NotImplementedError('Show log method should be implemented by subclasses')

class Action(metaclass=ActionMeta):
    action_type = None

    def perform(self, performer: Performer) -> ActionOutput:
        raise NotImplementedError('Perform method should be implemented by subclasses')

class ExecuteShellCommandAction(Action):
    action_type = ActionType.EXECUTE_SHELL_COMMAND

    def __init__(self, command_line: str):
        self.input = ActionInput(command_line)

    def perform(self, performer: Performer, verbose: bool = False) -> ActionOutput:
        command = self.input.prompt
        performer.show_log(f'running command: {command}')
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        if verbose:
            performer.show_log(f'command result: {result.stdout}')

        success = result.returncode == 0
        return ActionOutput(success=success, message=result.stdout)
 