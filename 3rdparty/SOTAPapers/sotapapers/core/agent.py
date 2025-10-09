import loguru

from sotapapers.core.action import ActionInput, ActionOutput, ActionType, Performer, ExecuteShellCommandAction
from sotapapers.core.settings import Settings

class Agent(Performer):
    def __init__(self, settings: Settings, logger: loguru.logger, name: str):
        self.settings = settings
        self.log = logger
        self.name = name

    def show_log(self, message: str, level: str = 'INFO'):
        self.log.log(level, message)
        
    def perform_action(self, action_type: ActionType, input: ActionInput) -> ActionOutput:
        if action_type == ActionType.EXECUTE_SHELL_COMMAND:
            action = ExecuteShellCommandAction(input.prompt)
        else:
            raise NotImplementedError('Perform action method should be implemented by subclasses')
        return action.perform(self)
