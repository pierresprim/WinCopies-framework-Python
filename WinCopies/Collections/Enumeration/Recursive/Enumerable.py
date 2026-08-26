from __future__ import annotations

from abc import abstractmethod
from typing import final



from WinCopies import IInterface, Abstract
from WinCopies.Bool import NullableBoolean, ToNullableBoolean

from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, Enumerable, EnumeratorProvider, AbstractEnumerator, GetIterationInactiveError
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyEnumerable, IRecursiveEnumerationHandlerBase, IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler
from WinCopies.Collections.Linked.Singly import Stack

from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import Converter, Function, Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Discard import IDisposable
from WinCopies.Typing.Pairing import DualResult, CreateDualResult

class IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems](IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetEnumerator(self) -> IEnumerator[TEnumerationItems]:
        ...
    
    @abstractmethod
    def GetEnumerationItems(self, enumerationItems: TEnumerationItems) -> IEnumerable[TEnumerationItems]:
        ...

    @abstractmethod
    def MoveNext(self) -> bool:
        ...
    
    @abstractmethod
    def GetStackItem(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> TStackItems:
        ...
    @abstractmethod
    def GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TEnumerationItems]:
        ...
    @abstractmethod
    def GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        ...
    
    @abstractmethod
    def Push(self, item: TStackItems) -> None:
        ...

    @abstractmethod
    def TryPeek(self) -> INullable[TStackItems]:
        ...
    
    @abstractmethod
    def TryPop(self) -> INullable[TStackItems]:
        ...
    
    @abstractmethod
    def OnEnteringSublevel(self, item: TEnumerationItems) -> bool|None:
        ...
    @abstractmethod
    def OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        ...
    
    @abstractmethod
    def OnEnteringMainLevel(self, item: TEnumerationItems) -> bool|None:
        ...
    @abstractmethod
    def OnExitingMainLevel(self, cookie: TCookie) -> bool:
        ...

class IRecursiveEnumerationDelegate[T](IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetOrder(self) -> EnumerationOrder:
        ...

    @abstractmethod
    def GetCurrent(self) -> T:
        ...

    @abstractmethod
    def MoveNext(self) -> bool:
        ...

@final
class _NullRecursiveEnumerationDelegate[T](Abstract, IRecursiveEnumerationDelegate[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def Initialize(self) -> None: pass
    
    def GetOrder(self) -> EnumerationOrder: return EnumerationOrder.Null
    
    def GetCurrent(self) -> T: raise GetIterationInactiveError()
    
    def MoveNext(self) -> bool: return False
    
    def Dispose(self) -> None: pass
class _RecursiveEnumerationDelegate[TEnumerationItems, TCookie, TStackItems](Abstract, IRecursiveEnumerationDelegate[TEnumerationItems]):
    def __init__(self, cookieProvider: Function[IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]]) -> None:
        super().__init__()

        self.__moveNext: Function[bool]|None = None
        self.__currentEnumerator: IEnumerator[TEnumerationItems]|None = None
        self.__cookieProvider: Function[IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]] = cookieProvider
    
    @final
    def _GetCookie(self) -> IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]:
        return self.__cookieProvider()
    
    def _OnEnteringLevel(self, currentItem: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> None:
        cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems] = self._GetCookie()

        cookie.Push(cookie.GetStackItem(currentItem, enumerator))
    def _OnExitingLevel(self, enumerator: IEnumerator[TEnumerationItems]) -> None: pass
    
    @final
    def __ProcessEnumerator(self, currentItem: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems], cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> NullableBoolean:
        while enumerator.MoveNext():
            match cookie.OnEnteringSublevel(currentItem):
                case None: return NullableBoolean.Null
                
                case True:
                    self._OnEnteringLevel(currentItem, enumerator)
                    
                    return NullableBoolean.BoolTrue
                
                case _: pass
        
        return NullableBoolean.BoolFalse
    
    @final
    def _TryEnterLevel(self) -> NullableBoolean:
        def getEnumerator(cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]]|None:
            enumerator: IEnumerator[TEnumerationItems]|None = self._GetCurrentEnumerator()

            if enumerator is None: return None
            
            item: TEnumerationItems|None = enumerator.GetCurrent()

            return None if item is None else CreateDualResult(item, cookie.GetEnumerationItems(item).GetEnumerator())
        
        cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems] = self._GetCookie()
        result: DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]]|None = getEnumerator(cookie)

        return NullableBoolean.BoolFalse if result is None else self.__ProcessEnumerator(result.GetKey(), result.GetValue(), cookie)
    
    def _Loop(self, result: INullable[TStackItems]) -> bool|None:
        def moveNext(enumerator: IEnumerator[TEnumerationItems]) -> bool: return enumerator.MoveNext()
        
        def tryPop(cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> INullable[TStackItems]: return cookie.TryPop()
        
        def loop(cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> bool|None:
            nonlocal result

            loopResult: bool|None = cookie.OnExitingSublevel(cookie.GetStackItemAsCookie(result.GetValue()))

            if loopResult is None: return False
            
            while (result := tryPop(cookie)).HasValue():
                if loopResult is True and moveNext(enumerator := cookie.GetStackItemAsEnumerator(result.GetValue())):
                    self._OnExitingLevel(enumerator)

                    return True

                if (loopResult := cookie.OnExitingSublevel(cookie.GetStackItemAsCookie(result.GetValue()))) is None: return False
            
            return None
        
        cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems] = self._GetCookie()
        loopResult: bool|None = cookie.OnExitingSublevel(cookie.GetStackItemAsCookie(result.GetValue()))
        
        if loopResult is None: return False
        
        enumerator: IEnumerator[TEnumerationItems]|None = None
        
        if loopResult is False:
            if (result := tryPop(cookie)).HasValue(): return loop(cookie)
        
        if (result := tryPop(cookie)).HasValue():
            if moveNext(enumerator := cookie.GetStackItemAsEnumerator(result.GetValue())):
                self._OnExitingLevel(enumerator)

                return True
            
            return loop(cookie)
        
        return None
    
    @abstractmethod
    def _MoveNext(self) -> bool:
        ...

    @final
    def _UpdateMoveNext(self, func: Function[bool]) -> None:
        self.__moveNext = func
    
    @final
    def _GetCurrentEnumerator(self) -> IEnumerator[TEnumerationItems]|None:
        return self.__currentEnumerator
    @final
    def _SetCurrentEnumerator(self, enumerator: IEnumerator[TEnumerationItems]) -> None:
        self.__currentEnumerator = enumerator
    
    def Initialize(self) -> None:
        self._GetCookie().Initialize()

        self.__moveNext = self._MoveNext
    
    @final
    def GetCurrent(self) -> TEnumerationItems:
        enumerator: IEnumerator[TEnumerationItems]|None = self.__currentEnumerator

        if enumerator is None: raise GetIterationInactiveError()

        return enumerator.GetCurrent()
    
    @final
    def MoveNext(self) -> bool: return False if self.__moveNext is None else self.__moveNext()
    
    def Dispose(self) -> None:
        self._GetCookie().Dispose()

        self.__currentEnumerator = None
        self.__moveNext = None

@final
class _FIFO[TEnumerationItems, TCookie, TStackItems](_RecursiveEnumerationDelegate[TEnumerationItems, TCookie, TStackItems]):
    def __init__(self, cookieProvider: Function[IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]]) -> None:
        super().__init__(cookieProvider)
        
        self.__first: TStackItems|None = None
    
    def GetOrder(self) -> EnumerationOrder: return EnumerationOrder.FIFO
    
    def _OnEnteringLevel(self, currentItem: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> None:
        super()._OnEnteringLevel(currentItem, enumerator)

        self._SetCurrentEnumerator(enumerator)
    def _OnExitingLevel(self, enumerator: IEnumerator[TEnumerationItems]) -> None:
        super()._OnExitingLevel(enumerator)

        self._SetCurrentEnumerator(enumerator)
    
    def _MoveNext(self) -> bool:
        def setCurrentEnumerator(value: IEnumerator[TEnumerationItems]) -> IEnumerator[TEnumerationItems]:
            self._SetCurrentEnumerator(value)

            return value
        
        def moveNext(current: TEnumerationItems, currentEnumerator: IEnumerator[TEnumerationItems]|None, cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> bool:
            def moveNext() -> bool:
                match self._TryEnterLevel():
                    case NullableBoolean.BoolTrue: return True
                    case NullableBoolean.Null: return False
                    
                    case _: pass
                
                result: INullable[TStackItems] = cookie.TryPeek()

                if result.HasValue():
                    if cookie.GetStackItemAsEnumerator(result.GetValue()).MoveNext(): return True
                    
                    loopResult: bool|None = self._Loop(result)

                    if loopResult is not None: return loopResult
            
                first: TStackItems|None = self.__first

                if not (first is None or cookie.OnExitingMainLevel(cookie.GetStackItemAsCookie(first))): return False

                self._UpdateMoveNext(self._MoveNext)

                return self._MoveNext()
            
            if currentEnumerator is None: return False
            
            self.__first = cookie.GetStackItem(current, currentEnumerator)
            
            self._UpdateMoveNext(moveNext)

            return True
        
        current: TEnumerationItems|None = None
        currentEnumerator: IEnumerator[TEnumerationItems]|None = None
        cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems] = self._GetCookie()
        enumerator: IEnumerator[TEnumerationItems] = cookie.GetEnumerator()

        while cookie.MoveNext() and (current := (currentEnumerator := setCurrentEnumerator(enumerator)).GetCurrent()) is not None:
            match ToNullableBoolean(cookie.OnEnteringMainLevel(current)):
                case NullableBoolean.BoolTrue:
                    if moveNext(current, currentEnumerator, cookie): return True
                
                case NullableBoolean.Null: return False
                
                case _: pass
        
        return False
    
    def Dispose(self) -> None:
        super().Dispose()

        self.__first = None
@final
class _LIFO[T](_RecursiveEnumerationDelegate[T, T, DualResult[T, IEnumerator[T]]]):
    def __init__(self, cookieProvider: Function[IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]]]) -> None:
        super().__init__(cookieProvider)
        
        self.__first: DualResult[T, IEnumerator[T]]|None = None
    
    def GetOrder(self) -> EnumerationOrder: return EnumerationOrder.LIFO
    
    def _MoveNext(self) -> bool:
        def tryEnterLevel() -> NullableBoolean: return self._TryEnterLevel()
        
        def getEnumerator(value: INullable[DualResult[T, IEnumerator[T]]]) -> IEnumerator[T]: return value.GetValue().GetValue()
        
        def setCurrentEnumerator(value: IEnumerator[T]) -> IEnumerator[T]:
            self._SetCurrentEnumerator(value)

            return value
        
        def moveNext(current: T, currentEnumerator: IEnumerator[T]|None, cookie: IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]]) -> bool|None:
            def moveNext() -> bool:
                def _tryEnterLevel() -> bool|None:
                    _result: NullableBoolean = tryEnterLevel()

                    match _result:
                        case NullableBoolean.BoolTrue:
                            while _result == NullableBoolean.BoolTrue: _result = tryEnterLevel()
                            
                            if _result == NullableBoolean.Null: return False
                            
                            self._SetCurrentEnumerator(getEnumerator(cookie.TryPeek()))
                        
                        case NullableBoolean.Null: return False

                        case _: return None

                    return True
                
                result: INullable[DualResult[T, IEnumerator[T]]] = cookie.TryPeek()

                if result.HasValue():
                    loopResult: bool|None = None

                    if getEnumerator(result).MoveNext():
                        if (loopResult := _tryEnterLevel()) is not None: return loopResult
                    
                    if (loopResult := self._Loop(result)) is False: return False
                    
                    if loopResult is True and (loopResult := _tryEnterLevel()) is not None: return loopResult

                first: DualResult[T, IEnumerator[T]]|None = self.__first

                if not (first is None or cookie.OnExitingMainLevel(cookie.GetStackItemAsCookie(first))): return False

                self._UpdateMoveNext(self._MoveNext)

                return self._MoveNext()
            
            if currentEnumerator is None: return None
            
            self.__first = cookie.GetStackItem(current, currentEnumerator)

            result: NullableBoolean = tryEnterLevel()

            match result:
                case NullableBoolean.BoolTrue:
                    while result == NullableBoolean.BoolTrue: result = tryEnterLevel()
                    
                    if result == NullableBoolean.Null: return False
                    
                    self._SetCurrentEnumerator(getEnumerator(cookie.TryPeek()))
                
                    self._UpdateMoveNext(moveNext)
                
                case NullableBoolean.Null: return False
                
                case _: pass
            
            return True
        
        current: T|None = None
        currentEnumerator: IEnumerator[T]|None = None
        result: bool|None = None
        cookie: IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]] = self._GetCookie()
        enumerator: IEnumerator[T] = cookie.GetEnumerator()

        while cookie.MoveNext() and (current := (currentEnumerator := setCurrentEnumerator(enumerator)).GetCurrent()) is not None:
            match ToNullableBoolean(cookie.OnEnteringMainLevel(current)):
                case NullableBoolean.BoolTrue:
                    result = moveNext(current, currentEnumerator, cookie)

                    if result is None: continue

                    return result
                
                case NullableBoolean.Null: return False
                
                case _: pass
        
        return False
    
    def Dispose(self) -> None:
        super().Dispose()

        self.__first = None

class _IRecursiveEnumeratorBase[T, TCookie, TStackItems](IEnumerator[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        ...
    
    @abstractmethod
    def _GetCookie(self) -> IRecursiveEnumerationCookie[T, TCookie, TStackItems]:
        ...

class _IDelegate[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetEnumerator(self) -> IEnumerator[T]:
        ...

    @abstractmethod
    def GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        ...

    @abstractmethod
    def MoveNext(self) -> bool:
        ...
@final
class _Delegate[T](Abstract, _IDelegate[T]):
    def __init__(self, enumeratorProvider: Function[IEnumerator[T]], enumerationItemsProvider: Converter[T, IEnumerable[T]], moveNextAction: Function[bool]) -> None:
        super().__init__()

        self.__enumeratorProvider: Function[IEnumerator[T]] = enumeratorProvider
        self.__enumerationItemsProvider: Converter[T, IEnumerable[T]] = enumerationItemsProvider
        self.__moveNextAction: Function[bool] = moveNextAction
    
    def GetEnumerator(self) -> IEnumerator[T]: return self.__enumeratorProvider()

    def GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]: return self.__enumerationItemsProvider(enumerationItems)
    
    def MoveNext(self) -> bool: return self.__moveNextAction()

@final
class _NullRecursiveEnumerationHandler[TItem, TCookie](Abstract, IRecursiveEnumerationHandlerBase[TItem, TCookie]):
    def __init__(self) -> None: super().__init__()

    def OnStartingEnumeration(self) -> bool: return True
    
    def OnEnteringEnumerationLevel(self, item: TItem) -> None: pass
    def OnExitingEnumerationLevel(self, cookie: TCookie) -> None: pass
    
    def OnEnteringMainEnumerationLevel(self, item: TItem) -> bool|None: return True
    def OnExitingMainEnumerationLevel(self, cookie: TCookie) -> bool: return True
    
    def OnEnteringSubenumerationLevel(self, item: TItem) -> bool|None: return True
    def OnExitingSubenumerationLevel(self, cookie: TCookie) -> bool|None: return True
    
    def OnStoppedEnumeration(self) -> None: pass

class RecursiveEnumeratorBase[TItem, TCookie, TStackItems](AbstractEnumerator[TItem], _IRecursiveEnumeratorBase[TItem, TCookie, TStackItems]):
    @final
    class __Cookie[_TItem, _TCookie, _TStackItems](Abstract, IRecursiveEnumerationCookie[_TItem, _TCookie, _TStackItems]):
        def __init__(self, enumerator: RecursiveEnumeratorBase[_TItem, _TCookie, _TStackItems], delegate: _IDelegate[_TItem]) -> None:
            super().__init__()

            self.__enumerator: RecursiveEnumeratorBase[_TItem, _TCookie, _TStackItems] = enumerator
            self.__delegate: _IDelegate[_TItem] = delegate
            self.__enumerators: Stack[_TStackItems]|None = None
        
        def Initialize(self) -> None: self.__enumerators = Stack[_TStackItems]()

        def GetEnumerator(self) -> IEnumerator[_TItem]: return self.__delegate.GetEnumerator()
        
        def GetEnumerationItems(self, enumerationItems: _TItem) -> IEnumerable[_TItem]: return self.__delegate.GetEnumerationItems(enumerationItems)
        
        def MoveNext(self) -> bool: return self.__delegate.MoveNext()
        
        def GetStackItem(self, item: _TItem, enumerator: IEnumerator[_TItem]) -> _TStackItems: return self.__enumerator._GetStackItem(item, enumerator)
        def GetStackItemAsEnumerator(self, item: _TStackItems) -> IEnumerator[_TItem]: return self.__enumerator._GetStackItemAsEnumerator(item)
        def GetStackItemAsCookie(self, item: _TStackItems) -> _TCookie: return self.__enumerator._GetStackItemAsCookie(item)
        
        def Push(self, item: _TStackItems) -> None:
            if self.__enumerators is None: raise GetIterationInactiveError()
            
            self.__enumerators.Push(item)

        def TryPeek(self) -> INullable[_TStackItems]:
            if self.__enumerators is None: raise GetIterationInactiveError()
            
            return self.__enumerators.TryPeek()

        def TryPop(self) -> INullable[_TStackItems]:
            if self.__enumerators is None: raise GetIterationInactiveError()
            
            self.__enumerators.TryPop()

            return self.__enumerators.TryPeek()
    
        def OnEnteringSublevel(self, item: _TItem) -> bool|None:
            result: bool|None = self.__enumerator._OnEnteringSublevel(item)

            if result is True: self.__enumerator._OnEnteringLevel(item)

            return result
        def OnExitingSublevel(self, cookie: _TCookie) -> bool|None:
            result: bool|None = self.__enumerator._OnExitingSublevel(cookie)

            self.__enumerator._OnExitingLevel(cookie)
            
            return result
        
        def OnEnteringMainLevel(self, item: _TItem) -> bool|None:
            result: bool|None = self.__enumerator._OnEnteringMainLevel(item)
            
            if result is True: self.__enumerator._OnEnteringLevel(item)

            return result
        def OnExitingMainLevel(self, cookie: _TCookie) -> bool:
            result: bool = self.__enumerator._OnExitingMainLevel(cookie)

            self.__enumerator._OnExitingLevel(cookie)

            return result
        
        def Dispose(self) -> None:
            if self.__enumerators is not None:
                self.__enumerators.Clear()
                self.__enumerators = None
    
    def __init__(self, enumerator: IEnumerator[TItem], delegate: IRecursiveEnumerationDelegate[TItem]|None, handler: IRecursiveEnumerationHandlerBase[TItem, TCookie]|None) -> None:
        super().__init__(enumerator)
        
        self.__cookie: IRecursiveEnumerationCookie[TItem, TCookie, TStackItems] = RecursiveEnumeratorBase[TItem, TCookie, TStackItems].__Cookie(self, _Delegate[TItem](self._GetContainer, self._GetEnumerationItems, super()._MoveNextOverride))
        self.__moveNext: IRecursiveEnumerationDelegate[TItem] = _NullRecursiveEnumerationDelegate[TItem]() if delegate is None else delegate
        self.__handler: IRecursiveEnumerationHandlerBase[TItem, TCookie] = _NullRecursiveEnumerationHandler[TItem, TCookie]() if handler is None else handler
    
    @final
    def _GetCookie(self) -> IRecursiveEnumerationCookie[TItem, TCookie, TStackItems]:
        return self.__cookie
    
    @abstractmethod
    def _GetStackItem(self, item: TItem, enumerator: IEnumerator[TItem]) -> TStackItems:
        ...
    @abstractmethod
    def _GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TItem]:
        ...
    @abstractmethod
    def _GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        ...

    def _OnStarting(self) -> bool:
        if super()._OnStarting() and self.__handler.OnStartingEnumeration():
            self.__moveNext.Initialize()

            return True
        
        return False
    
    def _OnEnteringLevel(self, item: TItem) -> None:
        self.__handler.OnEnteringEnumerationLevel(item)
    def _OnExitingLevel(self, cookie: TCookie) -> None:
        self.__handler.OnExitingEnumerationLevel(cookie)
    
    def _OnEnteringSublevel(self, item: TItem) -> bool|None:
        return self.__handler.OnEnteringSubenumerationLevel(item)
    def _OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        return self.__handler.OnExitingSubenumerationLevel(cookie)
    
    def _OnEnteringMainLevel(self, item: TItem) -> bool|None:
        return self.__handler.OnEnteringMainEnumerationLevel(item)
    def _OnExitingMainLevel(self, cookie: TCookie) -> bool:
        return self.__handler.OnExitingMainEnumerationLevel(cookie)
    
    @final
    def _GetCurrent(self) -> TItem: return self.__moveNext.GetCurrent()
    
    def _MoveNextOverride(self) -> bool: return self.__moveNext.MoveNext()
    
    def _OnEnded(self) -> None:
        self.__moveNext.Dispose()

        super()._OnEnded()
    
    def _OnStopped(self) -> None: self.__handler.OnStoppedEnumeration()

class RecursiveEnumerator[T](RecursiveEnumeratorBase[T, None, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandler[T]|None = None) -> None: super().__init__(enumerator, _FIFO[T, None, IEnumerator[T]](self._GetCookie), handler)
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> IEnumerator[T]:
        return enumerator
    @final
    def _GetStackItemAsEnumerator(self, item: IEnumerator[T]) -> IEnumerator[T]:
        return item
    @final
    def _GetStackItemAsCookie(self, item: IEnumerator[T]) -> None:
        return None
class StackedRecursiveEnumerator[T](RecursiveEnumeratorBase[T, T, DualResult[T, IEnumerator[T]]]):
    def __init__(self, enumerator: IEnumerator[T], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> None:
        def getDelegate(enumerationOrder: EnumerationOrder, cookieProvider: Function[IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]]]) -> IRecursiveEnumerationDelegate[T]|None:
            match enumerationOrder:
                case EnumerationOrder.Null: return None
                
                case EnumerationOrder.FIFO: return _FIFO[T, T, DualResult[T, IEnumerator[T]]](cookieProvider)
                case EnumerationOrder.LIFO: return _LIFO[T](cookieProvider)
                
                case _: raise ValueError(enumerationOrder)
        
        super().__init__(enumerator, getDelegate(enumerationOrder, self._GetCookie), handler)
    
    @final
    def _CreateStack(self) -> Stack[DualResult[T, IEnumerator[T]]]:
        return Stack[DualResult[T, IEnumerator[T]]]()
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> DualResult[T, IEnumerator[T]]:
        return CreateDualResult(item, enumerator)
    @final
    def _GetStackItemAsEnumerator(self, item: DualResult[T, IEnumerator[T]]) -> IEnumerator[T]:
        return item.GetValue()
    @final
    def _GetStackItemAsCookie(self, item: DualResult[T, IEnumerator[T]]) -> T:
        return item.GetKey()

class _IEnumerator[T](IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
        ...

class DefaultRecursiveEnumerator[T](RecursiveEnumerator[T], _IEnumerator[T]):
    def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T], converter: Converter[T, IEnumerable[T]], handler: IRecursiveEnumerationHandler[T]|None = None) -> None:
        super().__init__(enumerator, handler)

        self.__enumerable: RecursivelyEnumerable[T] = enumerable
        self.__converter: Converter[T, IEnumerable[T]] = converter
    
    @final
    def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
        return self.__enumerable
    
    @final
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        return self.__converter(enumerationItems)
class DefaultRecursiveStackedEnumerator[T](StackedRecursiveEnumerator[T], _IEnumerator[T]):
    def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T], converter: Converter[T, IEnumerable[T]], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> None:
        super().__init__(enumerator, enumerationOrder, handler)

        self.__enumerable: RecursivelyEnumerable[T] = enumerable
        self.__converter: Converter[T, IEnumerable[T]] = converter
    
    @final
    def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
        return self.__enumerable
    
    @final
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        return self.__converter(enumerationItems)

@final
class _RecursivelyEnumerableUpdater[T](ValueFunctionUpdater[IEnumerable[T]]):
    def __init__(self, enumerable: IRecursivelyEnumerable[T], updater: Method[IFunction[IEnumerable[T]]]) -> None:
        super().__init__(updater)

        self.__enumerable: IRecursivelyEnumerable[T] = enumerable
    
    def _GetValue(self) -> IEnumerable[T]: return EnumeratorProvider[T](lambda: self.__enumerable.TryGetRecursiveEnumerator())

class RecursivelyEnumerable[T](Enumerable[T], IRecursivelyEnumerable[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IEnumerable[T]]) -> None: self.__recursive = func
        
        super().__init__()
    
        self.__recursive: IFunction[IEnumerable[T]] = _RecursivelyEnumerableUpdater[T](self, update) # type: ignore[no-redef]
    
    @abstractmethod
    def _AsRecursivelyEnumerable(self, container: T) -> IEnumerable[T]:
        ...

    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[T]: return self.__recursive.GetValue()
    
    def _TryGetRecursiveEnumerator(self, enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandler[T]|None) -> IEnumerator[T]|None:
        return DefaultRecursiveEnumerator[T](self, enumerator, self._AsRecursivelyEnumerable, handler)
    def _TryGetRecursiveStackedEnumerator(self, enumerator: IEnumerator[T], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[T]|None) -> IEnumerator[T]|None:
        return None if enumerationOrder == EnumerationOrder.Null else DefaultRecursiveStackedEnumerator[T](self, enumerator, self._AsRecursivelyEnumerable, enumerationOrder, handler)

    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        if enumerationOrder == EnumerationOrder.Null: return None
        
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        if enumerator is None: return None
        
        match enumerationOrder:
            case EnumerationOrder.FIFO: return self._TryGetRecursiveEnumerator(enumerator, handler)
            case EnumerationOrder.LIFO: return self._TryGetRecursiveStackedEnumerator(enumerator, EnumerationOrder.LIFO, None if handler is None else handler.AsStackHandler())
            
            case _: raise ValueError(enumerationOrder)
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        if enumerationOrder == EnumerationOrder.Null: return None
        
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        return None if enumerator is None else self._TryGetRecursiveStackedEnumerator(enumerator, enumerationOrder, handler)