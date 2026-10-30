from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Registry.Kernel import IItemRegistry, CreateItemRegistry
from WinCopies.Collections.Linked.Node import ILinkedNode
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Method
from WinCopies.Typing.Discard import IInvalidatable
from WinCopies.Typing.Monitoring import IWorker, IMonitor, Monitor

def GetRegistrationActiveError() -> InvalidOperationError:
    return InvalidOperationError("Registrars cannot be added or removed while a registration is in progress.")

class IInvalidationRegistrarBase(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Unregister(self) -> None:
        ...

class IInvalidationRegistrar(IInvalidationRegistrarBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Register(self, cookie: IInvalidatable) -> None:
        ...
class InvalidationRegistrar(Abstract, IInvalidationRegistrar):
    def __init__(self) -> None: super().__init__()

class IManagedInvalidationRegistrar(IInvalidationRegistrarBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Push(self, invalidationRegistrar: IInvalidationRegistrar) -> IRemovable:
        ...

    @abstractmethod
    def Register(self) -> None:
        ...

@final
class _RegistrarCookie(Abstract, IRemovable):
    def __init__(self, node: IRemovable, state: IWorker) -> None:
        super().__init__()

        self.__node: IRemovable = node
        self.__state: IWorker = state

    def Remove(self) -> None:
        if self.__state.IsBusy(): raise GetRegistrationActiveError()

        self.__node.Remove()

class ManagedInvalidationRegistrar(Abstract, IManagedInvalidationRegistrar):
    def __init__(self, cookie: IInvalidatable) -> None:
        super().__init__()

        self.__items: IItemRegistry[IInvalidationRegistrar] = CreateItemRegistry()
        self.__cookie: IInvalidatable = cookie
        self.__state: IMonitor = Monitor()

    @final
    def __Process(self, action: Method[IInvalidationRegistrar]) -> None:
        def register(node: ILinkedNode[IInvalidationRegistrar]) -> None: action(node.GetValue())
        
        node: ILinkedNode[IInvalidationRegistrar]|None = self.__items.TryGetFirstNode()

        if node is None: return
        
        register(node)

        while (node := node.GetNext()) is not None: register(node)

    @final
    def Push(self, invalidationRegistrar: IInvalidationRegistrar) -> IRemovable:
        if self.__state.IsBusy(): raise GetRegistrationActiveError()

        return _RegistrarCookie(self.__items.Push(invalidationRegistrar), self.__state)

    @final
    def Register(self) -> None:
        cookie: IInvalidatable = self.__cookie

        self.__state.Initialize()
        cookie.Initialize()

        self.__Process(lambda registrar: registrar.Register(cookie))
    @final
    def Unregister(self) -> None:
        self.__Process(lambda registrar: registrar.Unregister())

        self.__state.Dispose()
        self.__cookie.Dispose()