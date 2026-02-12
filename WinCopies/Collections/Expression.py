from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, EnumeratorProvider, EnumeratorBase, AbstractionEnumerator, GetEmptyEnumerable
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyEnumerable, IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler
from WinCopies.Collections.Enumeration.Recursive.Enumerable import RecursiveEnumerator, StackedRecursiveEnumerator
from WinCopies.Delegates import BoolFalse
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Converter, Function, Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult

class ICompositeExpressionNodeBase[TValue, TConnector](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetFirst(self) -> ICompositeExpression[TValue, TConnector]:
        pass
    @abstractmethod
    def GetLast(self) -> ICompositeExpression[TValue, TConnector]:
        pass

class ICompositeExpression[TValue, TConnector](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetValue(self) -> INullable[TValue]:
        pass
    @abstractmethod
    def TryGetItems(self) -> ICompositeExpressionNode[TValue, TConnector]|None:
        pass

    @abstractmethod
    def GetPrevious(self) -> IConnector[TValue, TConnector]|None:
        pass
    @abstractmethod
    def GetNext(self) -> IConnector[TValue, TConnector]|None:
        pass

    @abstractmethod
    def SetPrevious(self, value: TValue, connector: TConnector) -> None:
        pass
    @abstractmethod
    def SetNext(self, connector: TConnector, value: TValue) -> None:
        pass

    @abstractmethod
    def SetPreviousExpression(self, expression: ICompositeExpressionNode[TValue, TConnector], connector: TConnector) -> None:
        pass
    @abstractmethod
    def SetNextExpression(self, connector: TConnector, expression: ICompositeExpressionNode[TValue, TConnector]) -> None:
        pass

class ICompositeExpressionRoot[TValue, TConnector](ICompositeExpressionNodeBase[TValue, TConnector], IRecursivelyEnumerable[ICompositeExpression[TValue, TConnector]]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetRecursiveValueEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[ICompositeExpression[TValue, TConnector]]|None = None) -> IEnumerator[IKeyValuePair[TValue, INullable[TConnector]]]|None:
        pass
    @abstractmethod
    def TryGetRecursiveStackedValueEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[ICompositeExpression[TValue, TConnector]]|None = None) -> IEnumerator[IKeyValuePair[TValue, INullable[TConnector]]]|None:
        pass

class ICompositeExpressionNode[TValue, TConnector](ICompositeExpressionNodeBase[TValue, TConnector], IEnumerable[ICompositeExpression[TValue, TConnector]]):
    def __init__(self) -> None:
        super().__init__()

class IConnector[TValue, TConnector](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetConnector(self) -> TConnector:
        pass
    
    @abstractmethod
    def GetPrevious(self) -> ICompositeExpression[TValue, TConnector]:
        pass
    @abstractmethod
    def GetNext(self) -> ICompositeExpression[TValue, TConnector]:
        pass

class ConnectorCookie[TValue, TConnector](Abstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetConnector(self) -> Connector[TValue, TConnector]:
        pass

    @abstractmethod
    def SetPrevious(self, expression: CompositeExpressionBase[TValue, TConnector]) -> None:
        pass
    @abstractmethod
    def SetNext(self, expression: CompositeExpressionBase[TValue, TConnector]) -> None:
        pass
class Connector[TValue, TConnector](Abstract, IConnector[TValue, TConnector]):
    @final
    class _Cookie[_TValue, _TConnector](ConnectorCookie[_TValue, _TConnector]):
        def __init__(self, connector: Connector[_TValue, _TConnector]) -> None:
            super().__init__()

            self.__connector: Connector[_TValue, _TConnector] = connector
        
        def GetConnector(self) -> Connector[_TValue, _TConnector]:
            return self.__connector
        
        def SetPrevious(self, expression: CompositeExpressionBase[_TValue, _TConnector]) -> None:
            self.__connector._SetPrevious(expression)
        def SetNext(self, expression: CompositeExpressionBase[_TValue, _TConnector]) -> None:
            self.__connector._SetNext(expression)
    
    def __init__(self, previous: CompositeExpressionBase[TValue, TConnector], connector: TConnector, next: CompositeExpressionBase[TValue, TConnector]) -> None:
        super().__init__()

        self.__connector: TConnector = connector

        self.__previous: CompositeExpressionBase[TValue, TConnector] = previous
        self.__next: CompositeExpressionBase[TValue, TConnector] = next
    
    @final
    def _ToCookie(self) -> ConnectorCookie[TValue, TConnector]:
        return Connector._Cookie(self)
    
    @final
    def GetConnector(self) -> TConnector:
        return self.__connector
    
    @final
    def GetPrevious(self) -> CompositeExpressionBase[TValue, TConnector]:
        return self.__previous
    @final
    def GetNext(self) -> CompositeExpressionBase[TValue, TConnector]:
        return self.__next
    
    @final
    def _SetPrevious(self, expression: CompositeExpressionBase[TValue, TConnector]) -> None:
        self.__previous = expression
    @final
    def _SetNext(self, expression: CompositeExpressionBase[TValue, TConnector]) -> None:
        self.__next = expression

class ICompositeExpressionCookie[TValue, TConnector](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def SetFirst(self, expression: ICompositeExpression[TValue, TConnector]) -> None:
        pass
    @abstractmethod
    def SetLast(self, expression: ICompositeExpression[TValue, TConnector]) -> None:
        pass

class ICompositeExpressionBase[TValue, TConnector](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _OnFirstUpdated(self, expression: ICompositeExpression[TValue, TConnector]) -> None:
        pass
    @abstractmethod
    def _OnLastUpdated(self, expression: ICompositeExpression[TValue, TConnector]) -> None:
        pass

class _ICompositeExpressionBase[TValue, TConnector](ICompositeExpressionBase[TValue, TConnector]):
    @final
    class _PreviousValueConnector[_TValue, _TConnector](Connector[_TValue, _TConnector]):
        def __init__(self, value: _TValue, connector: _TConnector, next: CompositeExpressionBase[_TValue, _TConnector]) -> None:
            expression: CompositeExpressionBase[_TValue, _TConnector] = next._CreateFromValue(None, value, self._ToCookie())

            super().__init__(expression, connector, next)
        
        @staticmethod
        def CreateCookie(value: _TValue, connector: _TConnector, next: CompositeExpressionBase[_TValue, _TConnector]) -> ConnectorCookie[_TValue, _TConnector]:
            return _ICompositeExpressionBase._PreviousValueConnector(value, connector, next)._ToCookie()
    @final
    class _NextValueConnector[_TValue, _TConnector](Connector[_TValue, _TConnector]):
        def __init__(self, previous: CompositeExpressionBase[_TValue, _TConnector], connector: _TConnector, value: _TValue) -> None:
            expression: CompositeExpressionBase[_TValue, _TConnector] = previous._CreateFromValue(self._ToCookie(), value, None)

            super().__init__(previous, connector, expression)
        
        @staticmethod
        def CreateCookie(previous: CompositeExpressionBase[_TValue, _TConnector], connector: _TConnector, value: _TValue) -> ConnectorCookie[_TValue, _TConnector]:
            return _ICompositeExpressionBase._NextValueConnector(previous, connector, value)._ToCookie()
    
    @final
    class _PreviousConnector[_TValue, _TConnector](Connector[_TValue, _TConnector]):
        def __init__(self, expression: ICompositeExpressionNode[_TValue, _TConnector], connector: _TConnector, next: CompositeExpressionBase[_TValue, _TConnector]) -> None:
            _expression: CompositeExpressionBase[_TValue, _TConnector] = next._CreateFromExpression(None, expression, self._ToCookie())

            super().__init__(_expression, connector, next)
        
        @staticmethod
        def CreateCookie(expression: ICompositeExpressionNode[_TValue, _TConnector], connector: _TConnector, next: CompositeExpressionBase[_TValue, _TConnector]) -> ConnectorCookie[_TValue, _TConnector]:
            return _ICompositeExpressionBase._PreviousConnector(expression, connector, next)._ToCookie()
    @final
    class _NextConnector[_TValue, _TConnector](Connector[_TValue, _TConnector]):
        def __init__(self, previous: CompositeExpressionBase[_TValue, _TConnector], connector: _TConnector, expression: ICompositeExpressionNode[_TValue, _TConnector]) -> None:
            _expression: CompositeExpressionBase[_TValue, _TConnector] = previous._CreateFromExpression(self._ToCookie(), expression, None)

            super().__init__(previous, connector, _expression)
        
        @staticmethod
        def CreateCookie(previous: CompositeExpressionBase[_TValue, _TConnector], connector: _TConnector, expression: ICompositeExpressionNode[_TValue, _TConnector]) -> ConnectorCookie[_TValue, _TConnector]:
            return _ICompositeExpressionBase._NextConnector(previous, connector, expression)._ToCookie()
    
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _CreateFromValue(self, previous: ConnectorCookie[TValue, TConnector]|None, value: TValue, next: ConnectorCookie[TValue, TConnector]|None) -> CompositeExpressionBase[TValue, TConnector]:
        pass
    @abstractmethod
    def _CreateFromExpression(self, previous: ConnectorCookie[TValue, TConnector]|None, expression: ICompositeExpressionNode[TValue, TConnector], next: ConnectorCookie[TValue, TConnector]|None) -> CompositeExpressionBase[TValue, TConnector]:
        pass
class CompositeExpressionBase[TValue, TConnector](Abstract, _ICompositeExpressionBase[TValue, TConnector], ICompositeExpression[TValue, TConnector]):
    def __init__(self, previous: ConnectorCookie[TValue, TConnector]|None, next: ConnectorCookie[TValue, TConnector]|None) -> None:
        super().__init__()

        self.__previous: ConnectorCookie[TValue, TConnector]|None = previous
        self.__next: ConnectorCookie[TValue, TConnector]|None = next
    
    @final
    def __OnSetPrevious(self, connector: ConnectorCookie[TValue, TConnector]) -> None:
        previous: ConnectorCookie[TValue, TConnector]|None = self.__previous
        _connector: Connector[TValue, TConnector] = connector.GetConnector()

        if previous is None:
            self._OnFirstUpdated(_connector.GetPrevious())
        
        else:
            expression: CompositeExpressionBase[TValue, TConnector] = _connector.GetPrevious()

            previous.SetNext(expression)
            expression._SetPrevious(previous)

        self.__previous = connector
    @final
    def __OnSetNext(self, connector: ConnectorCookie[TValue, TConnector]) -> None:
        next: ConnectorCookie[TValue, TConnector]|None = self.__next
        _connector: Connector[TValue, TConnector] = connector.GetConnector()

        if next is None:
            self._OnLastUpdated(_connector.GetNext())
        
        else:
            expression: CompositeExpressionBase[TValue, TConnector] = _connector.GetNext()

            next.SetPrevious(expression)
            expression._SetNext(next)
        
        self.__next = connector
    
    @final
    def _SetPrevious(self, connector: ConnectorCookie[TValue, TConnector]) -> None:
        self.__previous = connector
    @final
    def _SetNext(self, connector: ConnectorCookie[TValue, TConnector]) -> None:
        self.__next = connector
    
    @final
    def GetPrevious(self) -> Connector[TValue, TConnector]|None:
        return None if self.__previous is None else self.__previous.GetConnector()
    @final
    def GetNext(self) -> Connector[TValue, TConnector]|None:
        return None if self.__next is None else self.__next.GetConnector()

    @final
    def SetPrevious(self, value: TValue, connector: TConnector) -> None:
        self.__OnSetPrevious(_ICompositeExpressionBase._PreviousValueConnector[TValue, TConnector].CreateCookie(value, connector, self))
    @final
    def SetNext(self, connector: TConnector, value: TValue) -> None:
        self.__OnSetNext(_ICompositeExpressionBase._NextValueConnector[TValue, TConnector].CreateCookie(self, connector, value))

    @final
    def SetPreviousExpression(self, expression: ICompositeExpressionNode[TValue, TConnector], connector: TConnector) -> None:
        self.__OnSetPrevious(_ICompositeExpressionBase._PreviousConnector[TValue, TConnector].CreateCookie(expression, connector, self))
    @final
    def SetNextExpression(self, connector: TConnector, expression: ICompositeExpressionNode[TValue, TConnector]) -> None:
        self.__OnSetNext(_ICompositeExpressionBase._NextConnector[TValue, TConnector].CreateCookie(self, connector, expression))

class CompositeExpressionValue[TValue, TConnector](CompositeExpressionBase[TValue, TConnector], ICompositeExpression[TValue, TConnector]):
    def __init__(self, previous: ConnectorCookie[TValue, TConnector]|None, value: TValue, next: ConnectorCookie[TValue, TConnector]|None) -> None:
        super().__init__(previous, next)

        self.__value: TValue = value
    
    @final
    def TryGetValue(self) -> INullable[TValue]:
        return GetNullable(self.__value)
    @final
    def TryGetItems(self) -> None:
        return None
class CompositeExpression[TValue, TConnector](CompositeExpressionBase[TValue, TConnector], ICompositeExpression[TValue, TConnector]):
    def __init__(self, previous: ConnectorCookie[TValue, TConnector]|None, expression: ICompositeExpressionNode[TValue, TConnector], next: ConnectorCookie[TValue, TConnector]|None) -> None:
        super().__init__(previous, next)

        self.__items: ICompositeExpressionNode[TValue, TConnector] = expression
    
    @final
    def TryGetValue(self) -> INullable[TValue]:
        return GetNullValue()
    @final
    def TryGetItems(self) -> ICompositeExpressionNode[TValue, TConnector]:
        return self.__items

class _ICompositeExpressionAbstract[TValue, TConnector](_ICompositeExpressionBase[TValue, TConnector]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetCookie(self) -> ICompositeExpressionCookie[TValue, TConnector]:
        pass
    
    @final
    def _CreateFromValue(self, previous: ConnectorCookie[TValue, TConnector]|None, value: TValue, next: ConnectorCookie[TValue, TConnector]|None) -> CompositeExpressionBase[TValue, TConnector]:
        return _CompositeExpressionValue(self._GetCookie, previous, value, next)
    @final
    def _CreateFromExpression(self, previous: ConnectorCookie[TValue, TConnector]|None, expression: ICompositeExpressionNode[TValue, TConnector], next: ConnectorCookie[TValue, TConnector]|None) -> CompositeExpressionBase[TValue, TConnector]:
        return _CompositeExpression(self._GetCookie, previous, expression, next)
    
    @final
    def _OnFirstUpdated(self, expression: ICompositeExpression[TValue, TConnector]) -> None:
        self._GetCookie().SetFirst(expression)
    @final
    def _OnLastUpdated(self, expression: ICompositeExpression[TValue, TConnector]) -> None:
        self._GetCookie().SetLast(expression)
@final
class _CompositeExpressionValue[TValue, TConnector](CompositeExpressionValue[TValue, TConnector], _ICompositeExpressionAbstract[TValue, TConnector]):
    def __init__(self, cookieProvider: Function[ICompositeExpressionCookie[TValue, TConnector]], previous: ConnectorCookie[TValue, TConnector]|None, value: TValue, next: ConnectorCookie[TValue, TConnector]|None) -> None:
        super().__init__(previous, value, next)

        self.__cookieProvider: Function[ICompositeExpressionCookie[TValue, TConnector]] = cookieProvider
    
    def _GetCookie(self) -> ICompositeExpressionCookie[TValue, TConnector]:
        return self.__cookieProvider()
@final
class _CompositeExpression[TValue, TConnector](CompositeExpression[TValue, TConnector], _ICompositeExpressionAbstract[TValue, TConnector]):
    def __init__(self, cookieProvider: Function[ICompositeExpressionCookie[TValue, TConnector]], previous: ConnectorCookie[TValue, TConnector]|None, expression: ICompositeExpressionNode[TValue, TConnector], next: ConnectorCookie[TValue, TConnector]|None) -> None:
        super().__init__(previous, expression, next)

        self.__cookieProvider: Function[ICompositeExpressionCookie[TValue, TConnector]] = cookieProvider
    
    def _GetCookie(self) -> ICompositeExpressionCookie[TValue, TConnector]:
        return self.__cookieProvider()

class _AbstractCompositeExpressionNode[TValue, TConnector](Abstract, ICompositeExpressionNodeBase[TValue, TConnector]):
    @final
    class __Cookie[_TValue, _TConnector](Abstract, ICompositeExpressionCookie[_TValue, _TConnector]):
        def __init__(self, expressionNode: _AbstractCompositeExpressionNode[_TValue, _TConnector]) -> None:
            super().__init__()

            self.__expressionNode: _AbstractCompositeExpressionNode[_TValue, _TConnector] = expressionNode
        
        def SetFirst(self, expression: ICompositeExpression[_TValue, _TConnector]) -> None:
            return self.__expressionNode._SetFirst(expression)
        def SetLast(self, expression: ICompositeExpression[_TValue, _TConnector]) -> None:
            return self.__expressionNode._SetLast(expression)
    
    def __init__(self, initial: ICompositeExpression[TValue, TConnector]) -> None:
        super().__init__()

        self.__cookie: ICompositeExpressionCookie[TValue, TConnector] = _AbstractCompositeExpressionNode[TValue, TConnector].__Cookie(self)

        self.__first: ICompositeExpression[TValue, TConnector] = initial
        self.__last: ICompositeExpression[TValue, TConnector] = initial
    
    @final
    def _GetCookie(self) -> ICompositeExpressionCookie[TValue, TConnector]:
        return self.__cookie
    
    @final
    def GetFirst(self) -> ICompositeExpression[TValue, TConnector]:
        return self.__first
    @final
    def GetLast(self) -> ICompositeExpression[TValue, TConnector]:
        return self.__last
    
    @final
    def _SetFirst(self, expression: ICompositeExpression[TValue, TConnector]) -> None:
        self.__first = expression
    @final
    def _SetLast(self, expression: ICompositeExpression[TValue, TConnector]) -> None:
        self.__last = expression

class CompositeExpressionEnumerator[TValue, TConnector](EnumeratorBase[ICompositeExpression[TValue, TConnector]]):
    def __init__(self, node: ICompositeExpressionNodeBase[TValue, TConnector]) -> None:
        super().__init__()

        self.__node: ICompositeExpressionNodeBase[TValue, TConnector] = node
        self.__current: ICompositeExpression[TValue, TConnector]|None = None
        self.__moveNext: Function[bool] = BoolFalse
    
    @final
    def IsResetSupported(self) -> bool:
        return True
    
    @final
    def GetCurrent(self) -> ICompositeExpression[TValue, TConnector]|None:
        return self.__current
    
    def _OnStarting(self) -> bool:
        def moveNext() -> bool:
            def moveNext() -> bool:
                if self.__current is None:
                    return False
                
                connector: IConnector[TValue, TConnector]|None = self.__current.GetNext()

                if connector is None:
                    return False
                
                self.__current = connector.GetNext()

                return True

            self.__current = self.__node.GetFirst()
            self.__moveNext = moveNext

            return True

        if super()._OnStarting():
            self.__moveNext = moveNext

            return True
        
        return False
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__current = None
        self.__moveNext = BoolFalse
    def _OnStopped(self) -> None:
        pass
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _ResetOverride(self) -> bool:
        return True
class CompositeExpressionValueEnumerator[TValue, TConnector](AbstractionEnumerator[ICompositeExpression[TValue, TConnector], IKeyValuePair[TValue, INullable[TConnector]]]):
    def __init__(self, enumerator: IEnumerator[ICompositeExpression[TValue, TConnector]]) -> None:
        super().__init__(enumerator)

        self.__current: IKeyValuePair[TValue, INullable[TConnector]]|None = None
    
    @final
    def GetCurrent(self) -> IKeyValuePair[TValue, INullable[TConnector]]|None:
        return self.__current
    
    def _MoveNextOverride(self) -> bool:
        while super()._MoveNextOverride():
            current: ICompositeExpression[TValue, TConnector]|None = self._GetEnumerator().GetCurrent()

            if current is None:
                return False
            
            value: INullable[TValue] = current.TryGetValue()

            if value.HasValue():
                connector: IConnector[TValue, TConnector]|None = current.GetNext()

                self.__current = DualResult[TValue, INullable[TConnector]](value.GetValue(), GetNullValue() if connector is None else GetNullable(connector.GetConnector()))

                return True
        
        return False
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__current = None
    def _OnStopped(self) -> None:
        pass
    
    def _ResetOverride(self) -> bool:
        return True

class CompositeExpressionRecursiveEnumerator[TValue, TConnector](RecursiveEnumerator[ICompositeExpression[TValue, TConnector]]):
    def __init__(self, enumerator: IEnumerator[ICompositeExpression[TValue, TConnector]], handler: IRecursiveEnumerationHandler[ICompositeExpression[TValue, TConnector]]|None = None) -> None:
        super().__init__(enumerator, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: ICompositeExpression[TValue, TConnector]) -> IEnumerable[ICompositeExpression[TValue, TConnector]]:
        items: ICompositeExpressionNode[TValue, TConnector]|None = enumerationItems.TryGetItems()

        return GetEmptyEnumerable() if items is None else items
class CompositeExpressionStackedRecursiveEnumerator[TValue, TConnector](StackedRecursiveEnumerator[ICompositeExpression[TValue, TConnector]]):
    def __init__(self, enumerator: IEnumerator[ICompositeExpression[TValue, TConnector]], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[ICompositeExpression[TValue, TConnector]]|None = None) -> None:
        super().__init__(enumerator, enumerationOrder, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: ICompositeExpression[TValue, TConnector]) -> IEnumerable[ICompositeExpression[TValue, TConnector]]:
        items: ICompositeExpressionNode[TValue, TConnector]|None = enumerationItems.TryGetItems()

        return GetEmptyEnumerable() if items is None else items

@final
class _RecursiveUpdater[TValue, TConnector](ValueFunctionUpdater[IEnumerable[ICompositeExpression[TValue, TConnector]]]):
    def __init__(self, enumerable: IRecursivelyEnumerable[ICompositeExpression[TValue, TConnector]], updater: Method[IFunction[IEnumerable[ICompositeExpression[TValue, TConnector]]]]) -> None:
        super().__init__(updater)

        self.__enumerable: IRecursivelyEnumerable[ICompositeExpression[TValue, TConnector]] = enumerable
    
    def _GetValue(self) -> IEnumerable[ICompositeExpression[TValue, TConnector]]:
        return EnumeratorProvider[ICompositeExpression[TValue, TConnector]](lambda: self.__enumerable.TryGetRecursiveEnumerator())
@final
class __IterableUpdater[TValue, TConnector](ValueFunctionUpdater[Iterable[ICompositeExpression[TValue, TConnector]]]):
    def __init__(self, root: ICompositeExpressionRoot[TValue, TConnector], updater: Method[IFunction[Iterable[ICompositeExpression[TValue, TConnector]]]]) -> None:
        super().__init__(updater)

        self.__root: ICompositeExpressionRoot[TValue, TConnector] = root
    
    def _GetValue(self) -> Iterable[ICompositeExpression[TValue, TConnector]]:
        return EnumeratorProvider[ICompositeExpression[TValue, TConnector]](lambda: self.__root.TryGetEnumerator())

class _CompositeExpressionRootBase[TValue, TConnector](_AbstractCompositeExpressionNode[TValue, TConnector], ICompositeExpressionRoot[TValue, TConnector]):
    def __init__(self, initial: ICompositeExpression[TValue, TConnector]) -> None:
        def updateRecursive(func: IFunction[IEnumerable[ICompositeExpression[TValue, TConnector]]]) -> None:
            self.__recursive = func
        def updateIterable(func: IFunction[Iterable[ICompositeExpression[TValue, TConnector]]]) -> None:
            self.__iterable = func
        
        super().__init__(initial)
    
        self.__recursive: IFunction[IEnumerable[ICompositeExpression[TValue, TConnector]]] = _RecursiveUpdater[TValue, TConnector](self, updateRecursive) # type: ignore[no-redef]
        self.__iterable: IFunction[Iterable[ICompositeExpression[TValue, TConnector]]] = __IterableUpdater[TValue, TConnector](self, updateIterable) # type: ignore[no-redef]
    
    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[ICompositeExpression[TValue, TConnector]]:
        return self.__recursive.GetValue()
    
    @final
    def AsIterable(self) -> Iterable[ICompositeExpression[TValue, TConnector]]:
        return self.__iterable.GetValue()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[ICompositeExpression[TValue, TConnector]]:
        return CompositeExpressionEnumerator[TValue, TConnector](self)
    
    @final
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[ICompositeExpression[TValue, TConnector]]|None = None) -> IEnumerator[ICompositeExpression[TValue, TConnector]]|None:
        if enumerationOrder == EnumerationOrder.Null:
            return None
        
        match enumerationOrder:
            case EnumerationOrder.FIFO:
                return CompositeExpressionRecursiveEnumerator[TValue, TConnector](self.TryGetEnumerator(), handler)
            case EnumerationOrder.LIFO:
                return self.TryGetRecursiveStackedEnumerator(EnumerationOrder.LIFO, None if handler is None else handler.AsStackHandler())
            case _:
                raise ValueError(enumerationOrder)
    @final
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[ICompositeExpression[TValue, TConnector]]|None = None) -> IEnumerator[ICompositeExpression[TValue, TConnector]]|None:
        return None if enumerationOrder == EnumerationOrder.Null else CompositeExpressionStackedRecursiveEnumerator(self.TryGetEnumerator(), enumerationOrder, handler)
    
    @final
    def TryGetRecursiveValueEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[ICompositeExpression[TValue, TConnector]]|None = None) -> IEnumerator[IKeyValuePair[TValue, INullable[TConnector]]]|None:
        enumerator: IEnumerator[ICompositeExpression[TValue, TConnector]]|None = self.TryGetRecursiveEnumerator(enumerationOrder, handler)

        return None if enumerator is None else CompositeExpressionValueEnumerator[TValue, TConnector](enumerator)
    @final
    def TryGetRecursiveStackedValueEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[ICompositeExpression[TValue, TConnector]]|None = None) -> IEnumerator[IKeyValuePair[TValue, INullable[TConnector]]]|None:
        enumerator: IEnumerator[ICompositeExpression[TValue, TConnector]]|None = self.TryGetRecursiveStackedEnumerator(enumerationOrder, handler)

        return None if enumerator is None else CompositeExpressionValueEnumerator[TValue, TConnector](enumerator)

class CompositeExpressionValueRoot[TValue, TConnector](_CompositeExpressionRootBase[TValue, TConnector]):
    def __init__(self, initial: TValue) -> None:
        super().__init__(_CompositeExpressionValue[TValue, TConnector](self._GetCookie, None, initial, None))
class CompositeExpressionRoot[TValue, TConnector](_CompositeExpressionRootBase[TValue, TConnector]):
    def __init__(self, initial: ICompositeExpressionNode[TValue, TConnector]) -> None:
        super().__init__(_CompositeExpression[TValue, TConnector](self._GetCookie, None, initial, None))

@final
class _IterableUpdater[TValue, TConnector](ValueFunctionUpdater[Iterable[ICompositeExpression[TValue, TConnector]]]):
    def __init__(self, enumerable: IEnumerable[ICompositeExpression[TValue, TConnector]], updater: Method[IFunction[Iterable[ICompositeExpression[TValue, TConnector]]]]) -> None:
        super().__init__(updater)

        self.__enumerable: IEnumerable[ICompositeExpression[TValue, TConnector]] = enumerable
    
    def _GetValue(self) -> Iterable[ICompositeExpression[TValue, TConnector]]:
        return EnumeratorProvider[ICompositeExpression[TValue, TConnector]](lambda: self.__enumerable.TryGetEnumerator())

class _CompositeExpressionNodeBase[TValue, TConnector](_AbstractCompositeExpressionNode[TValue, TConnector], ICompositeExpressionNode[TValue, TConnector]):
    def __init__(self, initial: ICompositeExpression[TValue, TConnector]) -> None:
        def updateIterable(func: IFunction[Iterable[ICompositeExpression[TValue, TConnector]]]) -> None:
            self.__iterable = func
        
        super().__init__(initial)

        self.__iterable: IFunction[Iterable[ICompositeExpression[TValue, TConnector]]] = _IterableUpdater[TValue, TConnector](self, updateIterable) # type: ignore[no-redef]
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[ICompositeExpression[TValue, TConnector]]|None:
        return CompositeExpressionEnumerator[TValue, TConnector](self)
    
    @final
    def AsIterable(self) -> Iterable[ICompositeExpression[TValue, TConnector]]:
        return self.__iterable.GetValue()

class CompositeExpressionValueNode[TValue, TConnector](_CompositeExpressionNodeBase[TValue, TConnector]):
    def __init__(self, initial: TValue) -> None:
        super().__init__(_CompositeExpressionValue[TValue, TConnector](self._GetCookie, None, initial, None))
class CompositeExpressionNode[TValue, TConnector](_CompositeExpressionNodeBase[TValue, TConnector]):
    def __init__(self, initial: ICompositeExpressionNode[TValue, TConnector]) -> None:
        super().__init__(_CompositeExpression[TValue, TConnector](self._GetCookie, None, initial, None))

def MakeCompositeExpressionRoot[TRoot, TValue, TConnector](constructor: Converter[TValue, TRoot], converter: Converter[TRoot, ICompositeExpressionRoot[TValue, TConnector]], connector: TConnector, *values: TValue) -> TRoot|None:
    set: TRoot|None = None
    action: Method[TValue]|None = None

    def _add(root: ICompositeExpressionRoot[TValue, TConnector], value: TValue) -> None:
        root.GetLast().SetNext(connector, value)
    def add(value: TValue) -> None:
        nonlocal set
        nonlocal action

        __set: TRoot = constructor(value)
        _set: ICompositeExpressionRoot[TValue, TConnector] = converter(__set)
        set = __set
        action = lambda condition: _add(_set, condition)

    action = add

    for value in values:
        action(value)
    
    return set