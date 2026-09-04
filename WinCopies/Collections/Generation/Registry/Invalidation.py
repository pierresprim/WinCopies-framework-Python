from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Generation.Registry import IInvalidationRegistrar, IManagedInvalidationRegistrar
from WinCopies.Collections.Generation.Registry.Kernel import IItemRegistry, CreateItemRegistry
from WinCopies.Collections.Linked.Node import ILinkedNode
from WinCopies.Typing.Delegate import Method
from WinCopies.Typing.Discard import IInvalidatable

class ManagedInvalidationRegistrar(Abstract, IManagedInvalidationRegistrar):
    def __init__(self, cookie: IInvalidatable) -> None:
        super().__init__()

        self.__items: IItemRegistry[IInvalidationRegistrar] = CreateItemRegistry()
        self.__cookie: IInvalidatable = cookie

    @final
    def __Process(self, action: Method[IInvalidationRegistrar]) -> None:
        def register(node: ILinkedNode[IInvalidationRegistrar]) -> None: action(node.GetValue())
        
        node: ILinkedNode[IInvalidationRegistrar]|None = self.__items.TryGetFirstNode()

        if node is None: return
        
        register(node)

        while (node := node.GetNext()) is not None: register(node)

    @final
    def Push(self, invalidationRegistrar: IInvalidationRegistrar) -> IRemovable:
        return self.__items.Push(invalidationRegistrar)

    @final
    def Register(self) -> None: self.__Process(lambda registrar: registrar.Register(self.__cookie))
    @final
    def Unregister(self) -> None: self.__Process(lambda registrar: registrar.Unregister())