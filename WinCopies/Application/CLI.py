import sys

from abc import abstractmethod
from argparse import ArgumentParser as ArgumentParserBase, Namespace, RawDescriptionHelpFormatter
from enum import Enum
from typing import final, cast, Callable

from WinCopies import IInterface, Abstract
from WinCopies.Application import IDescription, Description
from WinCopies.Application.Logging import ILogger, Logger
from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Linked.Singly import IReadOnlyEnumerableList, IEnumerableList, CreateEnumerableQueue
from WinCopies.Collections.Util import MakeSequence
from WinCopies.Typing.Delegate import Converter
from WinCopies.Typing.Object import PrimitiveType

class IParameterDescription(IDescription):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def HasKey(self) -> bool: ...

    @abstractmethod
    def GetType(self) -> PrimitiveType: ...

class ParameterDescriptionAbstract(Abstract, IParameterDescription):
    def __init__(self, description: IDescription) -> None:
        super().__init__()

        self.__description: IDescription = description
    
    @final
    def GetName(self) -> str: return self.__description.GetName()
    @final
    def GetDescription(self) -> str: return self.__description.GetDescription()
class ParameterDescriptionBase(ParameterDescriptionAbstract):
    def __init__(self, description: IDescription, type: PrimitiveType) -> None:
        super().__init__(description)

        self.__type: PrimitiveType = type
    
    @final
    def GetType(self) -> PrimitiveType: return self.__type

class ParameterDescription(ParameterDescriptionBase):
    def __init__(self, description: IDescription, type: PrimitiveType) -> None: super().__init__(description, type)

    @final
    def HasKey(self) -> bool: return False
class KeyedParameterDescription(ParameterDescriptionBase):
    def __init__(self, description: IDescription, type: PrimitiveType) -> None: super().__init__(description, type)

    @final
    def HasKey(self) -> bool: return True

class Flag(ParameterDescriptionAbstract):
    def __init__(self, description: IDescription) -> None: super().__init__(description)

    @final
    def HasKey(self) -> bool: return True

    @final
    def GetType(self) -> PrimitiveType: return PrimitiveType.Null

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

def GetAction(value: bool) -> IFlagAction: return GetTrueAction() if value else GetFalseAction()

class IStoreAction(IAction):
    def __init__(self) -> None: super().__init__()

    @final
    def GetActionKind(self) -> ActionKind: return ActionKind.Store

    @abstractmethod
    def GetArgumentCount(self) -> int: ...

class _DefaultStoreAction(Action, IStoreAction):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetArgumentCount(self) -> int: return 1
class StoreAction(Action, IStoreAction):
    def __init__(self, count: int) -> None:
        if count < 1: raise ValueError()

        super().__init__()

        self.__count: int = count
    
    @final
    def GetArgumentCount(self) -> int: return self.__count

__storeAction: IAction = _DefaultStoreAction()

def GetDefaultStoreAction() -> IAction: return __storeAction

class IParameter(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetKind(self) -> ParameterKind: ...

    @abstractmethod
    def GetDescription(self) -> IParameterDescription: ...

    @abstractmethod
    def GetAction(self) -> IAction: ...
class Parameter(Abstract, IParameter):
    def __init__(self, description: IParameterDescription, action: IAction) -> None:
        super().__init__()

        self.__description: IParameterDescription = description
        self.__action: IAction = action

    @final
    def GetDescription(self) -> IParameterDescription: return self.__description

    @final
    def GetAction(self) -> IAction: return self.__action

class PositionalParameter(Parameter):
    def __init__(self, description: IParameterDescription) -> None:
        if description.GetName().startswith('-'): raise ValueError()

        super().__init__(description, GetDefaultStoreAction())

    @final
    def GetKind(self) -> ParameterKind: return ParameterKind.Positional
class OptionalParameter(Parameter):
    def __init__(self, description: IParameterDescription, action: IAction) -> None: super().__init__(description, action)

    @final
    def GetKind(self) -> ParameterKind: return ParameterKind.Optional

class ICommand(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetParameters(self) -> IReadOnlyEnumerableList[IParameter]: ...

    @abstractmethod
    def AddPositional(self, description: IParameterDescription) -> None: ...
    
    @abstractmethod
    def AddOptional(self, description: IParameterDescription, action: IStoreAction) -> None: ...
    @abstractmethod
    def AddFlag(self, description: Flag, value: bool) -> None: ...
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
    def __Push(self, description: IParameterDescription, action: IAction) -> None:
        self.__params.Push(OptionalParameter(description, action))

    @final
    def GetParameters(self) -> IReadOnlyEnumerableList[IParameter]: return self.__params.AsReadOnly()

    @final
    def AddPositional(self, description: IParameterDescription) -> None:
        if description.HasKey(): raise ValueError("A positional parameter cannot have a key.")

        self.__params.Push(PositionalParameter(description))
    
    @final
    def AddOptional(self, description: IParameterDescription, action: IStoreAction) -> None:
        self.__Push(description, action)
    @final
    def AddFlag(self, description: IDescription, value: bool) -> None:
        self.__Push(Flag(description), GetAction(value))
class Subcommand(Command, ISubcommand):
    def __init__(self, delegate: IDelegate) -> None:
        super().__init__()

        self.__delegate: IDelegate = delegate
    
    @final
    def GetDescription(self) -> IDescription: return self.__delegate.GetDescription()

    @final
    def GetDelegate(self) -> Converter[Namespace, int]: return self.__delegate.Run

def _AddCommand(parser: ArgumentParserBase, command: ICommand) -> None:
    description: IParameterDescription|None = None
    
    def add(optional: bool) -> None:
        nonlocal description

        def add(nameOrFlags: ReadOnlyArray[str], action: Callable[[ReadOnlyArray[str], str], None], help: str) -> None:
            action(nameOrFlags, help)

        def getNameOrFlags(name: str, hasKey: bool) -> ReadOnlyArray[str]:
            def _getName(prefix: str, name: str) -> str: return prefix + name
            def getName() -> str: return _getName("--", name)

            return ((_getName('-', name[0]), getName()) if hasKey else MakeSequence(getName())) if optional else MakeSequence(name)
        def getAction(action: IAction, type: PrimitiveType) -> Callable[[ReadOnlyArray[str], str], None]:
            def getAction[T](action: Callable[[ReadOnlyArray[str], str], T]) -> Callable[[ReadOnlyArray[str], str], None]:
                def callAction(nameOrFlags: ReadOnlyArray[str], help: str) -> None:
                    action(nameOrFlags, help)
                
                return callAction

            match action.GetActionKind():
                case ActionKind.Flag: return getAction(lambda nameOrFlags, help: parser.add_argument(*nameOrFlags, action=f"store_{"true" if cast(IFlagAction, action).GetValue() else "false"}", help=help))
                case ActionKind.Store: return getAction(lambda nameOrFlags, help: parser.add_argument(*nameOrFlags, action="store", type=type.Map(), nargs=cast(IStoreAction, action).GetArgumentCount(), help=help))

                case _:
                    raise ValueError()
        
        add(getNameOrFlags((description := param.GetDescription()).GetName(), description.HasKey()), getAction(param.GetAction(), description.GetType()), description.GetDescription())
    
    for param in command.GetParameters().AsIterable():
        match param.GetKind():
            case ParameterKind.Positional: add(False)
            case ParameterKind.Optional: add(True)

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

        command.AddFlag(Description("verbose", "Verbose mode (debug logging)"), True)

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