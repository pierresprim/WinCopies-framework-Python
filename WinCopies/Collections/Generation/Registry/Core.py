from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Generation.Registry import IObjectMonitor, IObjectRegistry
from WinCopies.Collections.Generation.Registry.Kernel import IWeakReferenceRegistry, IItemRegistry, CreateWeakReferenceRegistry, CreateItemRegistry
from WinCopies.Collections.Iteration import PrependValues, Select
from WinCopies.Collections.Linked.Doubly import IReadOnlyList
from WinCopies.Collections.Linked.Node import ILinkedNode
from WinCopies.Collections.Util import MakeSequence
from WinCopies.Delegates import NoAction
from WinCopies.Typing.Delegate import Action, Method, Converter as ConverterDelegate
from WinCopies.Typing.Discard import IInvalidatable
from WinCopies.Typing.Object import IWeakReferenceRegister, IWeakReference, CreateWeakReferenceRegister

@final
class _Node(Abstract):
    def __init__(self, exception: Exception) -> None:
        super().__init__()

        self.__exception: Exception = exception

        self.__next: _Node|None = None

    def GetValue(self) -> Exception:
        return self.__exception

    def GetNext(self) -> _Node|None:
        return self.__next
    def SetNext(self, exception: Exception) -> _Node:
        next: _Node = _Node(exception)

        self.__next = next

        return next
@final
class _ExceptionQueue(Abstract):
    def __init__(self) -> None:
        def push(exception: Exception) -> None:
            def push(exception: Exception) -> None:
                last: _Node = self.__last # type: ignore[has-type]

                self.__last = last.SetNext(exception) # pyright: ignore[reportOptionalMemberAccess]

            first: _Node = _Node(exception)

            self.__first = first
            self.__last = first

            self.__push = push

        super().__init__()

        self.__first: _Node|None = None # type: ignore[no-redef, assignment]
        self.__last: _Node|None = None # type: ignore[no-redef, assignment]

        self.__push: Method[Exception] = push # type: ignore[no-redef]

    def Push(self, exception: Exception) -> None:
        self.__push(exception)

    def Build(self) -> Exception|None:
        def build(node: _Node|None) -> Generator[_Node]:
            while node is not None:
                yield node

                node = node.GetNext()
        
        first: _Node|None = self.__first

        if first is None: return None

        next: _Node|None = first.GetNext()

        return first.GetValue() if next is None else ExceptionGroup("Multiple exceptions occurred.", MakeSequence(*Select(PrependValues(build(next.GetNext()), first, next), lambda node: node.GetValue())))

class ObjectRegistryBase[TIn, TOut: IInvalidatable](Abstract, IObjectRegistry[TIn]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IWeakReferenceRegistry[TOut] = CreateWeakReferenceRegistry()

        self.__push: ConverterDelegate[TOut, INodeBase] = self.__PushFirst
        self.__clear: Action = NoAction
    
    @final
    def _GetItems(self) -> IReadOnlyList[TOut]:
        return self.__items.AsReadOnly()
    
    @final
    def __Push(self, obj: TOut) -> INodeBase:
        cookie: IWeakReferenceRegister[TOut] = CreateWeakReferenceRegister(obj)
        node: INodeBase = self.__items.Push(cookie)

        cookie.RegisterNode(self._GetRemovable(obj, node))

        return node
    @final
    def __PushFirst(self, obj: TOut) -> INodeBase:
        self.__push = self.__Push
        self.__clear = self.__Clear

        return self.__Push(obj)
    def _Push(self, item: TIn) -> INodeBase:
        return self.__push(self._Convert(item))
    
    def _GetRemovable(self, obj: TOut, node: INodeBase) -> IRemovable:
        return node
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        ...
    
    @final
    def __Clear(self) -> None:
        cookie: IWeakReference[TOut]|None = None
        exceptions: _ExceptionQueue = _ExceptionQueue()

        while (cookie := self.__items.TryRemoveFirst()) is not None:
            try: cookie.Invalidate()
            except Exception as e: exceptions.Push(e)
        
        self.__push = self.__PushFirst
        self.__clear = NoAction

        exception: Exception|None = exceptions.Build()

        if exception is not None: raise exception
    
    @final
    def RegisterObject(self, item: TIn) -> None: self._Push(item)
    
    def InvalidateObjects(self) -> None: self.__clear()
class ObjectRegistry[T](ObjectRegistryBase[T, IInvalidatable]):
    def __init__(self) -> None: super().__init__()

class InvalidatableObjectRegistry[T: IInvalidatable](ObjectRegistryBase[T, T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: T) -> T: return item

@final
class _CollectionFactoryCookie(Abstract, IRemovable):
    def __init__(self, node: IRemovable) -> None:
        super().__init__()

        self.__node: IRemovable = node

    def Remove(self) -> None: self.__node.Remove()

class ICollectionRegistry[T: IObjectMonitor](IObjectRegistry[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def RegisterMonitor(self, item: T) -> IRemovable:
        ...

    def RegisterObject(self, item: T) -> None: self.RegisterMonitor(item)
class CollectionRegistry[T: IObjectMonitor](Abstract, ICollectionRegistry[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IItemRegistry[T] = CreateItemRegistry()

    @final
    def __Register(self, item: T) -> IRemovable:
        return self.__items.Push(item)

    @final
    def _GetItems(self) -> IReadOnlyList[T]:
        return self.__items.AsReadOnly()

    @final
    def RegisterObject(self, item: T) -> None: self.__Register(item)
    @final
    def RegisterMonitor(self, item: T) -> IRemovable: return _CollectionFactoryCookie(self.__Register(item))

    def InvalidateObjects(self) -> None:
        node: ILinkedNode[T]|None = self.__items.TryGetFirstNode()

        while node is not None:
            node.GetValue().InvalidateObjects()

            node = node.GetNext()