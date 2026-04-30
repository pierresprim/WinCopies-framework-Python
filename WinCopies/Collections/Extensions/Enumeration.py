from __future__ import annotations

from abc import abstractmethod
from typing import final, Any
from weakref import ref, finalize, ReferenceType

from WinCopies import IInterface, IDisposableBase, Abstract
from WinCopies.Collections.Enumeration import IEnumerator, IDisposableEnumerator, IncrementalEnumerator, ToDisposableEnumerator
from WinCopies.Collections.Extensions import ITuple, IEnumeratorMonitor
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Linked.Doubly import IDoublyLinkedNode, IList, List
from WinCopies.Delegates import NoAction
from WinCopies.Typing.Delegate import Action, Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

class TupleEnumeratorBase[TItem, TList](IncrementalEnumerator[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def _GetMaxValue(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def _GetCurrent(self) -> TItem:
        return self._GetInnerContainer().GetAt(self._GetValue())
class TupleEnumerator[T](TupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        super().__init__(items)

@final
class _EnumeratorMonitor[T](Abstract, IEnumeratorMonitor[T]):
    def __init__(self, factory: IEnumeratorFactory[T]) -> None:
        super().__init__()

        self.__factory: IEnumeratorFactory[T] = factory
    
    def CreateEnumerator(self, items: ITuple[T]) -> IEnumerator[T]:
        return self.__factory.CreateEnumerator(items)
@final
class _EnumeratorMonitorUpdater[T](ValueFunctionUpdater[IEnumeratorMonitor[T]]):
    def __init__(self, factory: IEnumeratorFactory[T], updater: Method[IFunction[IEnumeratorMonitor[T]]]) -> None:
        super().__init__(updater)

        self.__factory: IEnumeratorFactory[T] = factory
    
    def _GetValue(self) -> IEnumeratorMonitor[T]:
        return _EnumeratorMonitor[T](self.__factory)

class _IRegister[T](IInterface):
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
class _Cookie[T](Abstract):
    @final
    class _Register[_T](Abstract, _IRegister[_T]):
        def __init__(self, enumerator: IDisposableEnumerator[_T], cookie: _Cookie[_T]) -> None:
            super().__init__()

            self.__enumerator: IDisposableEnumerator[_T] = enumerator
            self.__cookie: _Cookie[_T] = cookie
        
        def GetCookie(self) -> _Cookie[_T]:
            return self.__cookie
        
        def RegisterNode(self, node: IRemovable) -> None:
            self.__cookie._RegisterNode(self.__enumerator, node)
    
    def __init__(self, enumerator: IDisposableEnumerator[T]) -> None:
        super().__init__()

        self.__ref: ReferenceType[IDisposableEnumerator[T]] = ref(enumerator)
        self.__finalizer: _Finalizer|None = None
    
    def TryGetValue(self) -> IDisposableEnumerator[T]|None:
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
    def Create(enumerator: IDisposableEnumerator[T]) -> _IRegister[T]:
        return _Cookie._Register[T](enumerator, _Cookie[T](enumerator))

class IObjectMonitor(IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def InvalidateObjects(self) -> None:
        pass

class IEnumeratorFactory[T](IEnumeratorMonitor[T], IObjectMonitor):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def RegisterObject(self, enumerator: IEnumerator[T]) -> None:
        pass

    @abstractmethod
    def AsMonitor(self) -> IEnumeratorMonitor[T]:
        pass
class EnumeratorFactory[T](Abstract, IEnumeratorFactory[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IEnumeratorMonitor[T]]) -> None:
            self.__monitor = func
        
        super().__init__()

        self.__enumerators: IList[_Cookie[T]] = List[_Cookie[T]]()

        self.__push: Method[IDisposableEnumerator[T]] = self.__PushFirst
        self.__clear: Action = NoAction

        self.__monitor: IFunction[IEnumeratorMonitor[T]] = _EnumeratorMonitorUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def __Push(self, enumerator: IDisposableEnumerator[T]) -> None:
        cookie: _IRegister[T] = _Cookie[T].Create(enumerator)
        node: IDoublyLinkedNode[_Cookie[T]] = self.__enumerators.AddLast(cookie.GetCookie())

        cookie.RegisterNode(node)
    @final
    def __PushFirst(self, enumerator: IDisposableEnumerator[T]) -> None:
        self.__clear = self.__Clear

        self.__Push(enumerator)
    def _PushEnumerator(self, enumerator: IEnumerator[T]) -> None:
        self.__push(ToDisposableEnumerator(enumerator))
    
    @final
    def __Clear(self) -> None:
        for cookie in self.__enumerators.AsQueuedGenerator():
            cookie.Invalidate()
        
        self.__push = self.__PushFirst
        self.__clear = NoAction
    
    @final
    def RegisterObject(self, enumerator: IEnumerator[T]) -> None:
        self._PushEnumerator(enumerator)
    
    @final
    def CreateEnumerator(self, items: ITuple[T]) -> IEnumerator[T]:
        enumerator: IEnumerator[T] = TupleEnumerator[T](items)

        self._PushEnumerator(enumerator)

        return enumerator
    
    def InvalidateObjects(self) -> None:
        self.__clear()
    
    @final
    def AsMonitor(self) -> IEnumeratorMonitor[T]:
        return self.__monitor.GetValue()