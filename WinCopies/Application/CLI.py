from __future__ import annotations

import sys

from abc import abstractmethod
from argparse import ArgumentParser as ArgumentParserBase, Namespace, RawDescriptionHelpFormatter
from enum import Enum
from typing import final, cast, Callable, Type

from WinCopies import IInterface, Abstract, TryConvertToInt
from WinCopies.Application import IDescription, Description
from WinCopies.Application.Logging import ILogger, Logger
from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Linked.Singly import IReadOnlyEnumerableList, IEnumerableList, CreateEnumerableQueue
from WinCopies.Collections.Util import MakeSequence
from WinCopies.Delegates import Try
from WinCopies.Typing.Delegate import Action as _Action, Method, Converter, Predicate
from WinCopies.Typing.Object import PrimitiveType, PrimitiveValue

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

class StoredParameterDescriptionBase[T: PrimitiveValue](ParameterDescriptionAbstract):
    def __init__(self, description: IDescription, action: IOptionalAction[T]) -> None:
        super().__init__(description)

        self.__action: IOptionalAction[T] = action

    @final
    def GetAction(self) -> IOptionalAction[T]:
        return self.__action
    
    @final
    def GetType(self) -> PrimitiveType: return PrimitiveType.TryMapFromType(self.GetAction().GetArgumentType())

class StoredParameterDescription[T: PrimitiveValue](StoredParameterDescriptionBase[T]):
    def __init__(self, description: IDescription, action: IOptionalAction[T]) -> None: super().__init__(description, action)

    @final
    def HasKey(self) -> bool: return False
class KeyedStoredParameterDescription[T: PrimitiveValue](StoredParameterDescriptionBase[T]):
    def __init__(self, description: IDescription, action: IOptionalAction[T]) -> None: super().__init__(description, action)

    @final
    def HasKey(self) -> bool: return True

def CreateOptionalParameterDescription[T: PrimitiveValue](description: IDescription, default: T, keyed: bool = False) -> StoredParameterDescriptionBase[T]:
    return (KeyedStoredParameterDescription[T] if keyed else StoredParameterDescription[T])(description, OptionalAction[T](default))
def CreateOptionalParameter[T: PrimitiveValue](description: IDescription, default: T, keyed: bool = False) -> OptionalParameter[T]:
    return OptionalParameter[T](CreateOptionalParameterDescription(description, default, keyed))

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
    def IsRequired(self) -> bool: ...

    @abstractmethod
    def GetArgumentCount(self) -> int: ...
class IOptionalAction[T: PrimitiveValue](IStoreAction):
    def __init__(self) -> None: super().__init__()

    @final
    def IsRequired(self) -> bool: return False
    
    @final
    def GetArgumentCount(self) -> int: return 1

    @abstractmethod
    def GetDefaultArgument(self) -> T: ...
    @abstractmethod
    def GetArgumentType(self) -> Type[T]: ...

class _StoreAction(Action, IStoreAction):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetArgumentCount(self) -> int: return 1

@final
class _DefaultStoreAction(_StoreAction):
    def __init__(self) -> None: super().__init__()

    def IsRequired(self) -> bool: return False
@final
class _DefaultRequiredAction(_StoreAction):
    def __init__(self) -> None: super().__init__()

    def IsRequired(self) -> bool: return True

class StoreActionBase(Action, IStoreAction):
    def __init__(self, count: int) -> None:
        if count < 1: raise ValueError()

        super().__init__()

        self.__count: int = count
    
    @final
    def GetArgumentCount(self) -> int: return self.__count

class StoreAction(StoreActionBase):
    def __init__(self, count: int) -> None: super().__init__(count)

    @final
    def IsRequired(self) -> bool: return False
class RequiredAction(StoreActionBase):
    def __init__(self, count: int) -> None: super().__init__(count)

    @final
    def IsRequired(self) -> bool: return True
class OptionalAction[T: PrimitiveValue](Action, IOptionalAction[T]):
    def __init__(self, default: T) -> None:
        super().__init__()

        self.__default: T = default

    @final
    def GetDefaultArgument(self) -> T: return self.__default
    @final
    def GetArgumentType(self) -> Type[T]: return type(self.GetDefaultArgument())

__storeAction: IAction = _DefaultStoreAction()
__requiredAction: IAction = _DefaultRequiredAction()

def GetDefaultStoreAction() -> IAction: return __storeAction
def GetDefaultRequiredAction() -> IAction: return __requiredAction

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
        if description.GetName().startswith('-'): raise ValueError()

        super().__init__()

        self.__description: IParameterDescription = description
        self.__action: IAction = action

    @final
    def GetDescription(self) -> IParameterDescription: return self.__description

    @final
    def GetAction(self) -> IAction: return self.__action

class PositionalParameter(Parameter):
    def __init__(self, description: IParameterDescription) -> None: super().__init__(description, GetDefaultStoreAction())

    @final
    def GetKind(self) -> ParameterKind: return ParameterKind.Positional
class NonRequiredParameter(Parameter):
    def __init__(self, description: IParameterDescription, action: IAction) -> None: super().__init__(description, action)

    @final
    def GetKind(self) -> ParameterKind: return ParameterKind.Optional
class OptionalParameter[T: PrimitiveValue](Abstract, IParameter):
    def __init__(self, description: StoredParameterDescriptionBase[T]) -> None:
        super().__init__()

        self.__description: StoredParameterDescriptionBase[T] = description

    @final
    def GetKind(self) -> ParameterKind: return ParameterKind.Optional

    @final
    def GetDescription(self) -> IParameterDescription: return self.__description

    @final
    def GetAction(self) -> IAction: return self.__description.GetAction()

class ICommand(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetParameters(self) -> IReadOnlyEnumerableList[IParameter]: ...

    @abstractmethod
    def AddPositional(self, description: IParameterDescription) -> None: ...
    
    @abstractmethod
    def AddNonRequired(self, description: IParameterDescription, action: IStoreAction|None = None) -> None: ...
    @abstractmethod
    def AddOptional(self, description: IDescription, default: PrimitiveValue, keyed: bool = False) -> None: ...

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
    def __PushParameter(self, parameter: IParameter) -> None:
        self.__params.Push(parameter)
    @final
    def __Push(self, description: IParameterDescription, action: IAction) -> None:
        self.__PushParameter(NonRequiredParameter(description, action))

    @final
    def GetParameters(self) -> IReadOnlyEnumerableList[IParameter]: return self.__params.AsReadOnly()

    @final
    def AddPositional(self, description: IParameterDescription) -> None:
        if description.HasKey(): raise ValueError("A positional parameter cannot have a key.")

        self.__PushParameter(PositionalParameter(description))
    
    @final
    def AddNonRequired(self, description: IParameterDescription, action: IStoreAction|None = None) -> None:
        self.__Push(description, GetDefaultStoreAction() if action is None else action)
    @final
    def AddOptional(self, description: IDescription, default: PrimitiveValue, keyed: bool = False) -> None:
        self.__PushParameter(CreateOptionalParameter(description, default, keyed))
    
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
        def getAction(action: IAction, t: PrimitiveType) -> Callable[[ReadOnlyArray[str], str], None]:
            def getAction[T](action: Callable[[ReadOnlyArray[str], str], T]) -> Callable[[ReadOnlyArray[str], str], None]:
                def callAction(nameOrFlags: ReadOnlyArray[str], help: str) -> None: action(nameOrFlags, help)
                
                return callAction

            match action.GetActionKind():
                case ActionKind.Flag: return getAction(lambda nameOrFlags, help: parser.add_argument(*nameOrFlags, action=f"store_{"true" if cast(IFlagAction, action).GetValue() else "false"}", help=help))
                case ActionKind.Store:
                    def addArgument(nameOrFlags: ReadOnlyArray[str], actionName: str, action: IStoreAction, t: type, help: str) -> None:
                        if isinstance(action, IOptionalAction):
                            parser.add_argument(*nameOrFlags, action=actionName, type=t, default=action.GetDefaultArgument(), nargs=1, help=help)

                        else:
                            parser.add_argument(*nameOrFlags, action=actionName, type=t, nargs=action.GetArgumentCount(), required=action.IsRequired(), help=help)
                    
                    return lambda nameOrFlags, help: addArgument(nameOrFlags, "store", cast(IStoreAction, action), t.Map(), help)

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

def ReadInt(message: str, errorMessage: str = "Invalid value; an integer is expected.") -> int:
    def read() -> int|None: return TryConvertToInt(input(message))
        
    value: int|None = read()
    
    while value is None:
        print(errorMessage)
        
        value = read()
    
    return value

def AskConfirmation(message: str, info: str = " [y]/any other key: ", value: str = "y") -> bool:
    return input(message + info) == value

def AskInt(message: str, predicate: Predicate[int], errorMessage: str = "The value is out of range.") -> int:
    value: int = 0
    
    def loop() -> int: return ReadInt(message)
    
    value = loop()
    
    while predicate(value):
        print(errorMessage)
        
        value = loop()
    
    return value

def Process(action: _Action, message: str = "Continue?", info: str = " [y]/any other key: ", value: str = "y") -> None:
    while AskConfirmation(message, info, value): action()

def DoProcess(action: _Action, message: str = "Continue?", info: str = " [y]/any other key: ", value: str = "y") -> None:
    action()
    
    Process(action, message, info, value)

def TryMessage(action: _Action, onError: Method[Exception], message: str = "Continue?") -> bool|None:
    return Try(action, onError, lambda: AskConfirmation(message))