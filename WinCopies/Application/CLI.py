import sys

from abc import abstractmethod
from argparse import ArgumentParser as ArgumentParserBase, Namespace, RawDescriptionHelpFormatter
from enum import Enum
from typing import final, cast

from WinCopies import IInterface, Abstract
from WinCopies.Application import IDescription, Description
from WinCopies.Application.Logging import ILogger, Logger
from WinCopies.Collections.Linked.Singly import IReadOnlyEnumerableList, IEnumerableList, CreateEnumerableQueue
from WinCopies.Typing.Delegate import Converter

class IDelegate(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetDescription(self) -> IDescription: ...

    @abstractmethod
    def Run(self, args: Namespace) -> int: ...
class Delegate(Abstract, IDelegate):
    def __init__(self, description: IDescription, log: ILogger) -> None:
        super().__init__()

        self.__description: IDescription = description
        self.__log: ILogger = log
    
    @final
    def _GetLog(self) -> ILogger: return self.__log

    @final
    def GetDescription(self) -> IDescription: return self.__description

class ParameterKind(Enum):
    Null = 0
    Positional = 1
    Optional = 2

class ActionKind(Enum):
    Null = 0
    Flag = 1
    Store = 2

class IAction(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetActionKind(self) -> ActionKind: ...

class IFlagAction(IAction):
    def __init__(self) -> None: super().__init__()

    @final
    def GetActionKind(self) -> ActionKind: return ActionKind.Flag

    @abstractmethod
    def GetValue(self) -> bool: ...

class Action(Abstract, IAction):
    def __init__(self) -> None: super().__init__()

class _TrueAction(Action, IFlagAction):
    def __init__(self) -> None: super().__init__()

    @final
    def GetValue(self) -> bool: return True
class _FalseAction(Action, IFlagAction):
    def __init__(self) -> None: super().__init__()

    @final
    def GetValue(self) -> bool: return False

__trueAction: IFlagAction = _TrueAction()
__falseAction: IFlagAction = _FalseAction()

def GetTrueAction() -> IFlagAction: return __trueAction
def GetFalseAction() -> IFlagAction: return __falseAction

class StoreAction(Action):
    def __init__(self) -> None: super().__init__()

    @final
    def GetActionKind(self) -> ActionKind: return ActionKind.Store

__storeAction: IAction = StoreAction()

def GetDefaultStoreAction() -> IAction: return __storeAction

class IParameter(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetKind(self) -> ParameterKind: ...

    @abstractmethod
    def GetDescription(self) -> IDescription: ...

    @abstractmethod
    def GetAction(self) -> IAction: ...
class Parameter(Abstract, IParameter):
    def __init__(self, description: IDescription, action: IAction) -> None:
        super().__init__()

        self.__description: IDescription = description
        self.__action: IAction = action

    @final
    def GetDescription(self) -> IDescription: return self.__description

    @final
    def GetAction(self) -> IAction: return self.__action

class PositionalParameter(Parameter):
    def __init__(self, description: IDescription) -> None:
        if description.GetName().startswith('-'): raise ValueError()

        super().__init__(description, GetDefaultStoreAction())

    @final
    def GetKind(self) -> ParameterKind: return ParameterKind.Positional
class OptionalParameter(Parameter):
    def __init__(self, description: IDescription, action: IAction) -> None: super().__init__(description, action)

    @final
    def GetKind(self) -> ParameterKind: return ParameterKind.Optional

class ICommand(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetParameters(self) -> IReadOnlyEnumerableList[IParameter]: ...

    @abstractmethod
    def AddPositional(self, description: IDescription) -> None: ...
    @abstractmethod
    def AddOptional(self, description: IDescription, action: IAction) -> None: ...
class ISubcommand(ICommand):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetDescription(self) -> IDescription: ...

    @abstractmethod
    def GetDelegate(self) -> Converter[Namespace, int]: ...

class Command(Abstract, ICommand):
    def __init__(self) -> None:
        super().__init__()

        self.__params: IEnumerableList[IParameter] = CreateEnumerableQueue()

    @final
    def GetParameters(self) -> IReadOnlyEnumerableList[IParameter]: return self.__params.AsReadOnly()

    @final
    def AddPositional(self, description: IDescription) -> None:
        self.__params.Push(PositionalParameter(description))
    @final
    def AddOptional(self, description: IDescription, action: IAction) -> None:
        self.__params.Push(OptionalParameter(description, action))
class Subcommand(Command, ISubcommand):
    def __init__(self, delegate: IDelegate) -> None:
        super().__init__()

        self.__delegate: IDelegate = delegate
    
    @final
    def GetDescription(self) -> IDescription: return self.__delegate.GetDescription()

    @final
    def GetDelegate(self) -> Converter[Namespace, int]: return self.__delegate.Run

def _AddCommand(parser: ArgumentParserBase, command: ICommand) -> None:
    description: IDescription|None = None
    
    def add(prefix: str = '') -> None:
        nonlocal description

        def getActionName(action: IAction) -> str:
            match action.GetActionKind():
                case ActionKind.Flag: return f"store_{"true" if cast(IFlagAction, action).GetValue() else "false"}"
                case ActionKind.Store: return "store"

                case _:
                    raise ValueError()
        
        parser.add_argument(prefix + (description := param.GetDescription()).GetName(), action=getActionName(param.GetAction()), help=description.GetDescription())
    
    for param in command.GetParameters().AsIterable():
        match param.GetKind():
            case ParameterKind.Positional: add()
            case ParameterKind.Optional: add("--")

            case _: raise ValueError()

class ICommandCollection(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Add(self, command: ISubcommand) -> None: ...
class CommandCollection(Abstract, ICommandCollection):
    def __init__(self, parser: ArgumentParserBase) -> None:
        super().__init__()

        self.__parser = parser.add_subparsers(dest="command", help="Available commands")
    
    @final
    def Add(self, command: ISubcommand) -> None:
        description: IDescription = command.GetDescription()
        parser = self.__parser.add_parser(description.GetName(), help=description.GetDescription())

        _AddCommand(parser, command)

        parser.set_defaults(func=command.GetDelegate())

class IArgumentParser(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetCommands(self) -> ICommandCollection: ...

    @abstractmethod
    def ParseArgs(self) -> Namespace: ...

    @abstractmethod
    def PrintHelp(self) -> None: ...
class ArgumentParser(Abstract, IArgumentParser):
    def __init__(self, programDescription: IDescription, command: ICommand|None = None, epilog: str|None = None) -> None:
        super().__init__()

        parser: ArgumentParserBase = ArgumentParserBase(prog=programDescription.GetName(),
                                                             description=programDescription.GetDescription(),
                                                             formatter_class=RawDescriptionHelpFormatter,
                                                             epilog=epilog)
        
        if command is not None: _AddCommand(parser, command)
        
        self.__parser: ArgumentParserBase = parser
        self.__commands: ICommandCollection = CommandCollection(parser)
    
    @final
    def GetCommands(self) -> ICommandCollection: return self.__commands
    
    @final
    def ParseArgs(self) -> Namespace: return self.__parser.parse_args()

    @final
    def PrintHelp(self) -> None: self.__parser.print_help()

class ApplicationError(Exception):
    def __init__(self, *args: object) -> None: super().__init__(*args)

class Application(Abstract):
    def __init__(self) -> None:
        super().__init__()
        
        self.__log: ILogger = Logger(__name__)
        
        command: Command = Command()

        command.AddOptional(Description("verbose", "Verbose mode (debug logging)"), GetTrueAction())

        self.__parser: IArgumentParser = self._CreateParser(command)
    
    @abstractmethod
    def _CreateParser(self, command: ICommand) -> IArgumentParser:
        """Creates the arguments parser."""
        ...
    
    @final
    def _GetLog(self) -> ILogger:
        return self.__log
    
    @final
    def _GetParser(self) -> IArgumentParser:
        return self.__parser
    
    @final
    def Start(self) -> int:
        def _onError(msg: str, value: int) -> int:
            print(msg, file=sys.stderr)

            return value
        def onError(e: Exception, msg: str, value: int) -> int:
            return _onError(f"{msg}: {e}", value)

        parser: IArgumentParser = self._GetParser()
        args: Namespace = parser.ParseArgs()
        
        self._GetLog().SetLevel(args.verbose)
        
        try:
            if hasattr(args, "func"): return args.func(args) or 0
            
            parser.PrintHelp()

            return 2
        
        except ApplicationError as e: return onError(e, f"Application error", 3)
        except KeyboardInterrupt: return _onError("\nCanceled by user", 130) # Standard code for SIGINT
        except Exception as e: return onError(e, f"Unknown error", 4)