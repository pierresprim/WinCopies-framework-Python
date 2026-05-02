from __future__ import annotations

from abc import abstractmethod
from typing import final, Any
from weakref import ref, finalize, ReferenceType

from WinCopies import IInterface, IDisposableBase, Abstract
from WinCopies.Collections.Generation import IRemovable, INode
from WinCopies.Collections.Linked.Doubly import IDoublyLinkedNode, IReadOnlyList, IList, List
from WinCopies.Delegates import NoAction
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Action, Method, Function, Converter as ConverterDelegate, IFunction, ValueFunctionUpdater

class _IRegister[T: IDisposableBase](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetCookie(self) -> _Cookie[T]:
        pass
    
    @abstractmethod
    def RegisterNode(self, node: IRemovable) -> None:
        pass

@final
class _Finalizer(Abstract, IRemovable):
    def __init__(self, finalizer: finalize[Any, IDisposableBase]) -> None:
        super().__init__()

        self.__finalizer: finalize[Any, IDisposableBase] = finalizer
    
    def Remove(self) -> None:
        self.__finalizer.detach()

@final
class _Cookie[T: IDisposableBase](Abstract):
    @final
    class _Register[_T: IDisposableBase](Abstract, _IRegister[_T]):
        def __init__(self, obj: _T, cookie: _Cookie[_T]) -> None:
            super().__init__()

            self.__obj: _T = obj
            self.__cookie: _Cookie[_T] = cookie
        
        def GetCookie(self) -> _Cookie[_T]:
            return self.__cookie
        
        def RegisterNode(self, node: IRemovable) -> None:
            self.__cookie._RegisterNode(self.__obj, node)
    
    def __init__(self, obj: T) -> None:
        super().__init__()

        self.__ref: ReferenceType[T] = ref(obj)
        self.__finalizer: _Finalizer|None = None
    
    def TryGetValue(self) -> T|None:
        return self.__ref()
    
    def Invalidate(self) -> None:
        obj: IDisposableBase|None = self.TryGetValue()

        if obj is not None:
            obj.Dispose()

            finalizer: _Finalizer|None = self.__finalizer

            if finalizer is not None:
                finalizer.Remove()
    
    def _RegisterNode(self, obj: IDisposableBase, node: IRemovable) -> None:
        self.__finalizer = _Finalizer(finalize(obj, lambda: node.Remove()))

    @staticmethod
    def Create(obj: T) -> _IRegister[T]:
        return _Cookie._Register[T](obj, _Cookie[T](obj))

@final
class _ReadOnlyList[T: IDisposableBase](Abstract, IReadOnlyList[T]):
    def __init__(self, items: IList[_Cookie[T]]) -> None:
        super().__init__()

        self.__items: IList[_Cookie[T]] = items
    
    def __TryGetValue(self, getNode: Function[IDoublyLinkedNode[_Cookie[T]]|None]) -> INullable[T]:
        def tryGetValue() -> INullable[T]|None:
            node: IDoublyLinkedNode[_Cookie[T]]|None = getNode()

            if node is None:
                return GetNullValue()
            
            item: T|None = node.GetValue().TryGetValue()

            if item is None:
                node.Remove()
                
                return None

            return GetNullable(item)

        item: INullable[T]|None = tryGetValue()

        if item is None:
            while self.__items.HasItems() and (item := tryGetValue()) is None:
                pass
        
        return GetNullValue() if item is None else item
    
    def IsEmpty(self) -> bool:
        return self.__items.IsEmpty()
    
    def TryGetFirst(self) -> INullable[T]:
        return self.__TryGetValue(lambda: self.__items.GetFirst())
    def TryGetLast(self) -> INullable[T]:
        return self.__TryGetValue(lambda: self.__items.GetLast())
@final
class _ReadOnlyListUpdater[T: IDisposableBase](ValueFunctionUpdater[IReadOnlyList[T]]):
    def __init__(self, items: IList[_Cookie[T]], updater: Method[IFunction[IReadOnlyList[T]]]) -> None:
        super().__init__(updater)

        self.__items: IList[_Cookie[T]] = items
    
    def _GetValue(self) -> IReadOnlyList[T]:
        return _ReadOnlyList[T](self.__items)

class IObjectMonitor(IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def InvalidateObjects(self) -> None:
        pass
class IObjectFactory[T](IObjectMonitor):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def RegisterObject(self, item: T) -> None:
        pass

class ObjectFactoryBase[TIn, TOut: IDisposableBase](Abstract, IObjectFactory[TIn]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyList[TOut]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__items: IList[_Cookie[TOut]] = List[_Cookie[TOut]]()

        self.__push: ConverterDelegate[TOut, INode] = self.__PushFirst
        self.__clear: Action = NoAction

        self.__readOnly: IFunction[IReadOnlyList[TOut]] = _ReadOnlyListUpdater[TOut](self.__items, update) # type: ignore[no-redef]
    
    @final
    def _GetItems(self) -> IReadOnlyList[TOut]:
        return self.__readOnly.GetValue()
    
    @final
    def __Push(self, obj: TOut) -> INode:
        cookie: _IRegister[TOut] = _Cookie[TOut].Create(obj)
        node: IDoublyLinkedNode[_Cookie[TOut]] = self.__items.AddLast(cookie.GetCookie())

        cookie.RegisterNode(node)

        return node
    @final
    def __PushFirst(self, obj: TOut) -> INode:
        self.__clear = self.__Clear

        return self.__Push(obj)
    def _Push(self, item: TIn) -> INode:
        return self.__push(self._Convert(item))
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        pass
    
    @final
    def __Clear(self) -> None:
        for cookie in self.__items.AsQueuedGenerator():
            cookie.Invalidate()
        
        self.__push = self.__PushFirst
        self.__clear = NoAction
    
    @final
    def RegisterObject(self, item: TIn) -> None:
        self._Push(item)
    
    def InvalidateObjects(self) -> None:
        self.__clear()
class ObjectFactory[T](ObjectFactoryBase[T, IDisposableBase]):
    def __init__(self) -> None:
        super().__init__()

class DisposableObjectFactory[T: IDisposableBase](ObjectFactoryBase[T, T], IObjectFactory[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _Convert(self, item: T) -> T:
        return item