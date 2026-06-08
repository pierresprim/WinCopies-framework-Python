from abc import abstractmethod
from typing import final

from WinCopies import IInterface, IDisposableBase, Abstract
from WinCopies.Collections.Generation import IRemovable, INode
from WinCopies.Collections.Linked.Doubly import IDoublyLinkedNode, IReadOnlyList, IList, List
from WinCopies.Delegates import NoAction
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Action, Method, Function, Converter as ConverterDelegate, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Object import IWeakReferenceRegister, WeakReference, CreateWeakReferenceRegister

class CompositeRemovable[T: IDisposableBase](Abstract, IRemovable):
    def __init__(self, node: IDoublyLinkedNode[WeakReference[T]], obj: IRemovable) -> None:
        def remove() -> None:
            self.__node.Remove()
            self.__obj.Remove()

            self.__remove = NoAction

        super().__init__()

        self.__node: IRemovable = node
        self.__obj: IRemovable = obj
        
        self.__remove: Action = remove # type: ignore[no-redef]
    
    def Remove(self) -> None: self.__remove()

@final
class _ReadOnlyList[T: IDisposableBase](Abstract, IReadOnlyList[T]):
    def __init__(self, items: IList[WeakReference[T]]) -> None:
        super().__init__()

        self.__items: IList[WeakReference[T]] = items
    
    def __TryGetValue(self, getNode: Function[IDoublyLinkedNode[WeakReference[T]]|None]) -> INullable[T]:
        def tryGetValue() -> INullable[T]|None:
            node: IDoublyLinkedNode[WeakReference[T]]|None = getNode()

            if node is None: return GetNullValue()
            
            item: T|None = node.GetValue().TryGetValue()

            if item is None:
                node.Remove()
                
                return None

            return GetNullable(item)

        item: INullable[T]|None = tryGetValue()

        if item is None:
            while self.__items.HasItems() and (item := tryGetValue()) is None: pass
        
        return GetNullValue() if item is None else item
    
    def IsEmpty(self) -> bool: return self.__items.IsEmpty()
    
    def TryGetFirst(self) -> INullable[T]: return self.__TryGetValue(lambda: self.__items.GetFirst())
    def TryGetLast(self) -> INullable[T]: return self.__TryGetValue(lambda: self.__items.GetLast())
@final
class _ReadOnlyListUpdater[T: IDisposableBase](ValueFunctionUpdater[IReadOnlyList[T]]):
    def __init__(self, items: IList[WeakReference[T]], updater: Method[IFunction[IReadOnlyList[T]]]) -> None:
        super().__init__(updater)

        self.__items: IList[WeakReference[T]] = items
    
    def _GetValue(self) -> IReadOnlyList[T]: return _ReadOnlyList[T](self.__items)

class IObjectMonitor(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def InvalidateObjects(self) -> None:
        ...
class IObjectFactory[T](IObjectMonitor):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def RegisterObject(self, item: T) -> None:
        ...

class ObjectFactoryBase[TIn, TOut: IDisposableBase](Abstract, IObjectFactory[TIn]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyList[TOut]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__items: IList[WeakReference[TOut]] = List[WeakReference[TOut]]()

        self.__push: ConverterDelegate[TOut, INode] = self.__PushFirst
        self.__clear: Action = NoAction

        self.__readOnly: IFunction[IReadOnlyList[TOut]] = _ReadOnlyListUpdater[TOut](self.__items, update) # type: ignore[no-redef]
    
    @final
    def _GetItems(self) -> IReadOnlyList[TOut]:
        return self.__readOnly.GetValue()
    
    @final
    def __Push(self, obj: TOut) -> INode:
        cookie: IWeakReferenceRegister[TOut] = CreateWeakReferenceRegister(obj)
        node: IDoublyLinkedNode[WeakReference[TOut]] = self.__items.AddLast(cookie.GetCookie())

        cookie.RegisterNode(self._GetRemovable(obj, node))

        return node
    @final
    def __PushFirst(self, obj: TOut) -> INode:
        self.__clear = self.__Clear

        return self.__Push(obj)
    def _Push(self, item: TIn) -> INode:
        return self.__push(self._Convert(item))
    
    def _GetRemovable(self, obj: TOut, node: IDoublyLinkedNode[WeakReference[TOut]]) -> IRemovable:
        return node
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        ...
    
    @final
    def __Clear(self) -> None:
        for cookie in self.__items.AsQueuedGenerator():
            cookie.Invalidate()
        
        self.__push = self.__PushFirst
        self.__clear = NoAction
    
    @final
    def RegisterObject(self, item: TIn) -> None: self._Push(item)
    
    def InvalidateObjects(self) -> None: self.__clear()
class ObjectFactory[T](ObjectFactoryBase[T, IDisposableBase]):
    def __init__(self) -> None: super().__init__()

class DisposableObjectFactory[T: IDisposableBase](ObjectFactoryBase[T, T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: T) -> T: return item