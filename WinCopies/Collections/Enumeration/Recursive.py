from abc import abstractmethod
from collections.abc import Iterable
from typing import final



from WinCopies import IInterface, Abstract, NullableBoolean, ToNullableBoolean

from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, Enumerable, EnumeratorProvider, AbstractEnumerator, GetEnumerator
from WinCopies.Collections.Linked.Singly import Stack

from WinCopies.Typing import InvalidOperationError, INullable, IDisposable
from WinCopies.Typing.Delegate import Converter, Function, Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import DualResult

class IRecursivelyEnumerable[T](IEnumerable[T]):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        pass
    @final
    def GetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetRecursiveEnumerator(enumerationOrder, handler))

    @abstractmethod
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        pass
    @final
    def GetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetRecursiveStackedEnumerator(enumerationOrder, handler))

    @final
    def GetRecursiveEnumerable(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerable[T]:
        return EnumeratorProvider[T](lambda: self.TryGetRecursiveEnumerator(enumerationOrder, handler))
    @final
    def GetRecursiveStackedEnumerable(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerable[T]:
        return EnumeratorProvider[T](lambda: self.TryGetRecursiveStackedEnumerator(enumerationOrder, handler))
    
    @abstractmethod
    def AsRecursivelyEnumerable(self) -> IEnumerable[T]:
        pass
    def AsRecursivelyIterable(self) -> Iterable[T]:
        return self.AsRecursivelyEnumerable().AsIterable()

class IRecursiveEnumerationHandlerBase[TItem, TCookie](IInterface):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def OnStartingEnumeration(self) -> bool:
        pass
    
    @abstractmethod
    def OnEnteringEnumerationLevel(self, item: TItem) -> None:
        pass
    @abstractmethod
    def OnExitingEnumerationLevel(self, cookie: TCookie) -> None:
        pass
    
    @abstractmethod
    def OnEnteringMainEnumerationLevel(self, item: TItem) -> bool|None:
        pass
    @abstractmethod
    def OnExitingMainEnumerationLevel(self, cookie: TCookie) -> bool|None:
        pass
    
    @abstractmethod
    def OnEnteringSubenumerationLevel(self, item: TItem) -> bool|None:
        pass
    @abstractmethod
    def OnExitingSubenumerationLevel(self, cookie: TCookie) -> bool|None:
        pass
    
    @abstractmethod
    def OnStoppedEnumeration(self) -> None:
        pass

class IRecursiveEnumerationHandler[T](IRecursiveEnumerationHandlerBase[T, None]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[T]:
        pass
class IRecursiveStackedEnumerationHandler[T](IRecursiveEnumerationHandlerBase[T, T]):
    def __init__(self):
        super().__init__()

@final
class _Handler[T](Abstract, IRecursiveStackedEnumerationHandler[T]):
    def __init__(self, handler: IRecursiveEnumerationHandler[T]):
        super().__init__()

        self.__handler: IRecursiveEnumerationHandler[T] = handler
    
    def OnStartingEnumeration(self) -> bool:
        return self.__handler.OnStartingEnumeration()
    
    def OnEnteringEnumerationLevel(self, item: T) -> None:
        return self.__handler.OnEnteringEnumerationLevel(item)
    def OnExitingEnumerationLevel(self, cookie: T) -> None:
        return self.__handler.OnExitingEnumerationLevel(None)
    
    def OnEnteringMainEnumerationLevel(self, item: T) -> bool|None:
        return self.__handler.OnEnteringMainEnumerationLevel(item)
    def OnExitingMainEnumerationLevel(self, cookie: T) -> bool|None:
        return self.__handler.OnExitingMainEnumerationLevel(None)
    
    def OnEnteringSubenumerationLevel(self, item: T) -> bool|None:
        return self.__handler.OnEnteringSubenumerationLevel(item)
    def OnExitingSubenumerationLevel(self, cookie: T) -> bool|None:
        return self.__handler.OnExitingSubenumerationLevel(None)
    
    def OnStoppedEnumeration(self) -> None:
        self.__handler.OnStoppedEnumeration()

class RecursiveEnumerationHandler[T](Abstract, IRecursiveEnumerationHandler[T]):
    @final
    class __Updater(ValueFunctionUpdater[IRecursiveStackedEnumerationHandler[T]]):
        def __init__(self, handler: IRecursiveEnumerationHandler[T], updater: Method[IFunction[IRecursiveStackedEnumerationHandler[T]]]):
            super().__init__(updater)

            self.__handler: IRecursiveEnumerationHandler[T] = handler
        
        def _GetValue(self) -> IRecursiveStackedEnumerationHandler[T]:
            return _Handler[T](self.__handler)
    
    def __init__(self):
        def update(func: IFunction[IRecursiveStackedEnumerationHandler[T]]) -> None:
            self.__handler = func
        
        super().__init__()
    
        self.__handler: IFunction[IRecursiveStackedEnumerationHandler[T]] = RecursiveEnumerationHandler[T].__Updater(self, update)
    
    @final
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[T]:
        return self.__handler.GetValue()

class RecursiveEnumerationHandlerAbstractorBase[TIn, TOut, TCookieIn, TCookieOut](Abstract, IRecursiveEnumerationHandlerBase[TIn, TCookieIn]):
    def __init__(self, handler: IRecursiveEnumerationHandlerBase[TOut, TCookieOut]):
        super().__init__()

        self.__handler: IRecursiveEnumerationHandlerBase[TOut, TCookieOut] = handler
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        pass
    
    @final
    def _GetHandler(self) -> IRecursiveEnumerationHandlerBase[TOut, TCookieOut]:
        return self.__handler

    @final
    def OnStartingEnumeration(self) -> bool:
        return self._GetHandler().OnStartingEnumeration()
    
    @final
    def OnEnteringEnumerationLevel(self, item: TIn) -> None:
        self._GetHandler().OnEnteringEnumerationLevel(self._Convert(item))
    
    @final
    def OnEnteringMainEnumerationLevel(self, item: TIn) -> bool|None:
        return self._GetHandler().OnEnteringMainEnumerationLevel(self._Convert(item))
    
    @final
    def OnEnteringSubenumerationLevel(self, item: TIn) -> bool|None:
        return self._GetHandler().OnEnteringSubenumerationLevel(self._Convert(item))
    
    @final
    def OnStoppedEnumeration(self) -> None:
        self._GetHandler().OnStoppedEnumeration()

class RecursiveEnumerationHandlerAbstractor[TIn, TOut](RecursiveEnumerationHandlerAbstractorBase[TIn, TOut, None, None], IRecursiveEnumerationHandler[TIn]):
    @final
    class __Updater(ValueFunctionUpdater[IRecursiveStackedEnumerationHandler[TOut]]):
        def __init__(self, handler: IRecursiveEnumerationHandler[TOut], updater: Method[IFunction[IRecursiveStackedEnumerationHandler[TOut]]]):
            super().__init__(updater)

            self.__handler: IRecursiveEnumerationHandler[TOut] = handler
        
        def _GetValue(self) -> IRecursiveStackedEnumerationHandler[TOut]:
            return _Handler[TOut](self.__handler)
    
    def __init__(self, handler: IRecursiveEnumerationHandler[TOut]):
        def update(func: IFunction[IRecursiveStackedEnumerationHandler[TOut]]) -> None:
            self.__handler = func

        super().__init__(handler)

        self.__handler: IFunction[IRecursiveStackedEnumerationHandler[TOut]] = RecursiveEnumerationHandlerAbstractor[TIn, TOut].__Updater(self, update)
    
    @final
    def OnExitingEnumerationLevel(self, cookie: None) -> None:
        self._GetHandler().OnExitingEnumerationLevel(cookie)
    
    @final
    def OnExitingMainEnumerationLevel(self, cookie: None) -> bool|None:
        return self._GetHandler().OnExitingMainEnumerationLevel(cookie)
    
    @final
    def OnExitingSubenumerationLevel(self, cookie: None) -> bool|None:
        return self._GetHandler().OnExitingSubenumerationLevel(cookie)
    
    @final
    def AsStackHandler(self) -> IRecursiveStackedEnumerationHandler[TOut]:
        return self.__handler.GetValue()
class RecursiveStackedEnumerationHandlerAbstractor[TIn, TOut](RecursiveEnumerationHandlerAbstractorBase[TIn, TOut, TIn, TOut], IRecursiveStackedEnumerationHandler[TIn]):
    def __init__(self, handler: IRecursiveStackedEnumerationHandler[TOut]):
        super().__init__(handler)
    
    @final
    def OnExitingEnumerationLevel(self, cookie: TIn) -> None:
        self._GetHandler().OnExitingEnumerationLevel(self._Convert(cookie))
    
    @final
    def OnExitingMainEnumerationLevel(self, cookie: TIn) -> bool|None:
        self._GetHandler().OnExitingMainEnumerationLevel(self._Convert(cookie))
    
    @final
    def OnExitingSubenumerationLevel(self, cookie: TIn) -> bool|None:
        self._GetHandler().OnExitingSubenumerationLevel(self._Convert(cookie))

class RecursiveEnumerationHandlerConverter[TIn, TOut](RecursiveEnumerationHandlerAbstractor[TIn, TOut]):
    def __init__(self, handler: IRecursiveEnumerationHandler[TOut], converter: Converter[TIn, TOut]):
        super().__init__(handler)

        self.__converter: Converter[TIn, TOut] = converter
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
class RecursiveStackedEnumerationHandlerConverter[TIn, TOut](RecursiveStackedEnumerationHandlerAbstractor[TIn, TOut]):
    def __init__(self, handler: IRecursiveStackedEnumerationHandler[TOut], converter: Converter[TIn, TOut]):
        super().__init__(handler)

        self.__converter: Converter[TIn, TOut] = converter
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)

@final
class _NullRecursiveEnumerationHandler[TItem, TCookie](Abstract, IRecursiveEnumerationHandlerBase[TItem, TCookie]):
    def __init__(self):
        super().__init__()

    def OnStartingEnumeration(self) -> bool:
        return True
    
    def OnEnteringEnumerationLevel(self, item: TItem) -> None:
        pass
    def OnExitingEnumerationLevel(self, cookie: TCookie) -> None:
        pass
    
    def OnEnteringMainEnumerationLevel(self, item: TItem) -> bool|None:
        return True
    def OnExitingMainEnumerationLevel(self, cookie: TCookie) -> bool|None:
        return True
    
    def OnEnteringSubenumerationLevel(self, item: TItem) -> bool|None:
        return True
    def OnExitingSubenumerationLevel(self, cookie: TCookie) -> bool|None:
        return True
    
    def OnStoppedEnumeration(self) -> None:
        pass

class IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems](IDisposable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetEnumerator(self) -> IEnumerator[TEnumerationItems]:
        pass
    
    @abstractmethod
    def GetEnumerationItems(self, enumerationItems: TEnumerationItems) -> IEnumerable[TEnumerationItems]:
        pass

    @abstractmethod
    def MoveNext(self) -> bool:
        pass
    
    @abstractmethod
    def GetStackItem(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> TStackItems:
        pass
    @abstractmethod
    def GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    @abstractmethod
    def GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        pass
    
    @abstractmethod
    def Push(self, item: TStackItems) -> None:
        pass

    @abstractmethod
    def TryPeek(self) -> INullable[TStackItems]:
        pass
    
    @abstractmethod
    def TryPop(self) -> INullable[TStackItems]:
        pass
    
    @abstractmethod
    def OnEnteringSublevel(self, item: TEnumerationItems) -> bool|None:
        pass
    @abstractmethod
    def OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        pass
    
    @abstractmethod
    def OnEnteringMainLevel(self, item: TEnumerationItems) -> bool|None:
        pass
    @abstractmethod
    def OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
        pass

class IRecursiveEnumerationDelegate[T](IDisposable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetOrder(self) -> EnumerationOrder:
        pass

    @abstractmethod
    def GetCurrent(self) -> T|None:
        pass

    @abstractmethod
    def MoveNext(self) -> bool:
        pass

@final
class _NullRecursiveEnumerationDelegate[T](Abstract, IRecursiveEnumerationDelegate[T]):
    def __init__(self):
        super().__init__()
    
    def Initialize(self) -> None:
        pass
    
    def GetOrder(self) -> EnumerationOrder:
        return EnumerationOrder.Null
    
    def GetCurrent(self) -> T|None:
        return None
    
    def MoveNext(self) -> bool:
        return False
    
    def Dispose(self) -> None:
        pass
class _RecursiveEnumerationDelegate[TEnumerationItems, TCookie, TStackItems](Abstract, IRecursiveEnumerationDelegate[TEnumerationItems]):
    def __init__(self, cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]):
        super().__init__()

        self.__moveNext: Function[bool]|None = None
        self.__currentEnumerator: IEnumerator[TEnumerationItems]|None = None
        self.__cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems] = cookie
    
    @final
    def _GetCookie(self) -> IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]:
        return self.__cookie
    
    def _OnEnteringLevel(self, currentItem: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> None:
        self._GetCookie().Push(self._GetCookie().GetStackItem(currentItem, enumerator))
    def _OnExitingLevel(self, enumerator: IEnumerator[TEnumerationItems]) -> None:
        pass
    
    @final
    def __ProcessEnumerator(self, currentItem: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> NullableBoolean:
        while enumerator.MoveNext():
            result: bool|None = self._GetCookie().OnEnteringSublevel(currentItem)
            
            if result is None:
                return NullableBoolean.Null
            
            if result is True:
                self._OnEnteringLevel(currentItem, enumerator)
                
                return NullableBoolean.BoolTrue
        
        return NullableBoolean.BoolFalse
    
    @final
    def _TryEnterLevel(self) -> NullableBoolean:
        def getEnumerator() -> DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]]|None:
            enumerator: IEnumerator[TEnumerationItems]|None = self._GetCurrentEnumerator()

            if enumerator is None:
                return None
            
            item: TEnumerationItems|None = enumerator.GetCurrent()

            return None if item is None else DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]](item, self._GetCookie().GetEnumerationItems(item).GetEnumerator())
        
        result: DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]]|None = getEnumerator()

        return NullableBoolean.BoolFalse if result is None else self.__ProcessEnumerator(result.GetKey(), result.GetValue())
            
    def _Loop(self, result: INullable[TStackItems]) -> bool|None:
        def moveNext(enumerator: IEnumerator[TEnumerationItems]) -> bool:
            return enumerator.MoveNext()
        
        def tryPop() -> INullable[TStackItems]:
            return self._GetCookie().TryPop()
        
        def loop() -> bool|None:
            nonlocal result
            nonlocal loopResult
            nonlocal enumerator

            if (loopResult := self._GetCookie().OnExitingSublevel(self._GetCookie().GetStackItemAsCookie(result.GetValue()))) is None:
                return False
            
            while (result := tryPop()).HasValue():
                if loopResult is True and moveNext(enumerator := self._GetCookie().GetStackItemAsEnumerator(result.GetValue())):
                    self._OnExitingLevel(enumerator)

                    return True

                if (loopResult := self._GetCookie().OnExitingSublevel(self._GetCookie().GetStackItemAsCookie(result.GetValue()))) is None:
                    return False
            
            return None
        
        loopResult: bool|None = self._GetCookie().OnExitingSublevel(self._GetCookie().GetStackItemAsCookie(result.GetValue()))
        
        if loopResult is None:
            return False
        
        enumerator: IEnumerator[TEnumerationItems]|None = None
        
        if loopResult is False:
            if (result := tryPop()).HasValue():
                return loop()
        
        if (result := tryPop()).HasValue():
            if moveNext(enumerator := self._GetCookie().GetStackItemAsEnumerator(result.GetValue())):
                self._OnExitingLevel(enumerator)

                return True
            
            return loop()
        
        return None
    
    @abstractmethod
    def _MoveNext(self) -> bool:
        pass

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
    def GetCurrent(self) -> TEnumerationItems|None:
        return None if self.__currentEnumerator is None else self.__currentEnumerator.GetCurrent()
    
    @final
    def MoveNext(self) -> bool:
        return False if self.__moveNext is None else self.__moveNext()
    
    def Dispose(self) -> None:
        self._GetCookie().Dispose()

        self.__currentEnumerator = None
        self.__moveNext = None

@final
class _FIFO[TEnumerationItems, TCookie, TStackItems](_RecursiveEnumerationDelegate[TEnumerationItems, TCookie, TStackItems]):
    def __init__(self, cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]):
        super().__init__(cookie)
        
        self.__first: TStackItems|None = None
    
    def GetOrder(self) -> EnumerationOrder:
        return EnumerationOrder.FIFO
    
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
        
        def moveNext() -> bool:
            match self._TryEnterLevel():
                case NullableBoolean.BoolTrue:
                    return True
                case NullableBoolean.Null:
                    return False
                case _:
                    pass
            
            result: INullable[TStackItems] = self._GetCookie().TryPeek()

            if result.HasValue():
                if self._GetCookie().GetStackItemAsEnumerator(result.GetValue()).MoveNext():
                    return True
                
                loopResult: bool|None = self._Loop(result)

                if loopResult is not None:
                    return loopResult
        
            first: TStackItems|None = self.__first

            if first is not None:
                self._GetCookie().OnExitingMainLevel(self._GetCookie().GetStackItemAsCookie(first))

            self._UpdateMoveNext(self._MoveNext)

            return self._MoveNext()
        
        current: TEnumerationItems|None = None
        currentEnumerator: IEnumerator[TEnumerationItems]|None = None

        while self._GetCookie().MoveNext() and (current := (currentEnumerator := setCurrentEnumerator(self._GetCookie().GetEnumerator())).GetCurrent()) is not None:
            match ToNullableBoolean(self._GetCookie().OnEnteringMainLevel(current)):
                case NullableBoolean.BoolTrue:
                    self.__first = self._GetCookie().GetStackItem(current, currentEnumerator)
                    
                    self._UpdateMoveNext(moveNext)

                    return True
                
                case NullableBoolean.Null:
                    return False
                
                case _:
                    continue
        
        return False
    
    def Dispose(self) -> None:
        super().Dispose()

        self.__first = None
@final
class _LIFO[T](_RecursiveEnumerationDelegate[T, T, DualResult[T, IEnumerator[T]]]):
    def __init__(self, cookie: IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]]):
        super().__init__(cookie)
        
        self.__first: DualResult[T, IEnumerator[T]]|None = None
    
    def GetOrder(self) -> EnumerationOrder:
        return EnumerationOrder.LIFO
    
    def _MoveNext(self) -> bool:
        def tryEnterLevel() -> NullableBoolean:
            return self._TryEnterLevel()
        
        def getEnumerator(value: INullable[DualResult[T, IEnumerator[T]]]) -> IEnumerator[T]:
            return value.GetValue().GetValue()
        
        def setCurrentEnumerator(value: IEnumerator[T]) -> IEnumerator[T]:
            self._SetCurrentEnumerator(value)

            return value
        
        def moveNext() -> bool:
            def _tryEnterLevel() -> bool|None:
                _result: NullableBoolean = tryEnterLevel()

                match _result:
                    case NullableBoolean.BoolTrue:
                        while _result == NullableBoolean.BoolTrue:
                            _result = tryEnterLevel()
                        
                        if _result == NullableBoolean.Null:
                            return False
                        
                        self._SetCurrentEnumerator(getEnumerator(self._GetCookie().TryPeek()))
                    case NullableBoolean.Null:
                        return False
                    case _:
                        return None

                return True
            
            result: INullable[DualResult[T, IEnumerator[T]]] = self._GetCookie().TryPeek()

            if result.HasValue():
                loopResult: bool|None = None

                if getEnumerator(result).MoveNext():
                    if (loopResult := _tryEnterLevel()) is not None:
                        return loopResult
                
                if (loopResult := self._Loop(result)) is False:
                    return False
                
                if loopResult is True and (loopResult := _tryEnterLevel()) is not None:
                    return loopResult

            first: DualResult[T, IEnumerator[T]]|None = self.__first

            if first is not None:
                self._GetCookie().OnExitingMainLevel(self._GetCookie().GetStackItemAsCookie(first))

            self._UpdateMoveNext(self._MoveNext)

            return self._MoveNext()
        
        current: T|None = None
        currentEnumerator: IEnumerator[T]|None = None

        while self._GetCookie().MoveNext() and (current := (currentEnumerator := setCurrentEnumerator(self._GetCookie().GetEnumerator())).GetCurrent()) is not None:
            match ToNullableBoolean(self._GetCookie().OnEnteringMainLevel(current)):
                case NullableBoolean.BoolTrue:
                    self.__first = self._GetCookie().GetStackItem(current, currentEnumerator)

                    result: NullableBoolean = tryEnterLevel()

                    match result:
                        case NullableBoolean.BoolTrue:
                            while result == NullableBoolean.BoolTrue:
                                result = tryEnterLevel()
                            
                            if result == NullableBoolean.Null:
                                return False
                            
                            self._SetCurrentEnumerator(getEnumerator(self._GetCookie().TryPeek()))
                        
                            self._UpdateMoveNext(moveNext)
                        case NullableBoolean.Null:
                            return False
                        case _:
                            pass

                    return True
                
                case NullableBoolean.Null:
                    return False
                
                case _:
                    continue
        
        return False
    
    def Dispose(self) -> None:
        super().Dispose()

        self.__first = None

class _RecursiveEnumeratorBase[T](IEnumerator[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        pass
class RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems](AbstractEnumerator[TEnumerationItems], _RecursiveEnumeratorBase[TEnumerationItems]):
    class _IDelegate(IInterface):
        def __init__(self):
            super().__init__()
        
        @abstractmethod
        def GetEnumerator(self) -> IEnumerator[TEnumerationItems]:
            pass

        @abstractmethod
        def GetEnumerationItems(self, enumerationItems: TEnumerationItems) -> IEnumerable[TEnumerationItems]:
            pass

        @abstractmethod
        def MoveNext(self) -> bool:
            pass
    @final
    class __Delegate(Abstract, _IDelegate):
        def __init__(self, enumeratorProvider: Function[IEnumerator[TEnumerationItems]], enumerationItemsProvider: Converter[TEnumerationItems, IEnumerable[TEnumerationItems]], moveNextAction: Function[bool]):
            super().__init__()

            self.__enumeratorProvider: Function[IEnumerator[TEnumerationItems]] = enumeratorProvider
            self.__enumerationItemsProvider: Converter[TEnumerationItems, IEnumerable[TEnumerationItems]] = enumerationItemsProvider
            self.__moveNextAction: Function[bool] = moveNextAction
        
        def GetEnumerator(self) -> IEnumerator[TEnumerationItems]:
            return self.__enumeratorProvider()

        def GetEnumerationItems(self, enumerationItems: TEnumerationItems) -> IEnumerable[TEnumerationItems]:
            return self.__enumerationItemsProvider(enumerationItems)
        
        def MoveNext(self) -> bool:
            return self.__moveNextAction()
    @final
    class __Cookie(Abstract, IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]):
        def __init__(self, enumerator: RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems], delegate: RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems]._IDelegate):
            super().__init__()

            self.__enumerator: RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems] = enumerator
            self.__delegate: RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems]._IDelegate = delegate
            self.__enumerators: Stack[TStackItems]|None = None
        
        def Initialize(self) -> None:
            self.__enumerators = Stack[TStackItems]()

        def GetEnumerator(self) -> IEnumerator[TEnumerationItems]:
            return self.__delegate.GetEnumerator()
        
        def GetEnumerationItems(self, enumerationItems: TEnumerationItems) -> IEnumerable[TEnumerationItems]:
            return self.__delegate.GetEnumerationItems(enumerationItems)
        
        def MoveNext(self) -> bool:
            return self.__delegate.MoveNext()
        
        def GetStackItem(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> TStackItems:
            return self.__enumerator._GetStackItem(item, enumerator)
        def GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TEnumerationItems]:
            return self.__enumerator._GetStackItemAsEnumerator(item)
        def GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
            return self.__enumerator._GetStackItemAsCookie(item)
        
        def Push(self, item: TStackItems) -> None:
            if self.__enumerators is None:
                raise InvalidOperationError()
            
            self.__enumerators.Push(item)

        def TryPeek(self) -> INullable[TStackItems]:
            if self.__enumerators is None:
                raise InvalidOperationError()
            
            return self.__enumerators.TryPeek()

        def TryPop(self) -> INullable[TStackItems]:
            if self.__enumerators is None:
                raise InvalidOperationError()
            
            self.__enumerators.TryPop()

            return self.__enumerators.TryPeek()
    
        def OnEnteringSublevel(self, item: TEnumerationItems) -> bool|None:
            if self.__enumerator._OnEnteringSublevel(item):
                self.__enumerator._OnEnteringLevel(item)

                return True
            
            return False
        def OnExitingSublevel(self, cookie: TCookie) -> bool|None:
            if self.__enumerator._OnExitingSublevel(cookie):
                self.__enumerator._OnExitingLevel(cookie)

                return True
            
            return False
        
        def OnEnteringMainLevel(self, item: TEnumerationItems) -> bool|None:
            if self.__enumerator._OnEnteringMainLevel(item):
                self.__enumerator._OnEnteringLevel(item)

                return True
            
            return False
        def OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
            if self.__enumerator._OnExitingMainLevel(cookie):
                self.__enumerator._OnExitingLevel(cookie)

                return True
            
            return False
        
        def Dispose(self) -> None:
            if self.__enumerators is not None:
                self.__enumerators.Clear()
                self.__enumerators = None
    
    def __init__(self, enumerator: IEnumerator[TEnumerationItems], delegate: IRecursiveEnumerationDelegate[TEnumerationItems]|None, handler: IRecursiveEnumerationHandlerBase[TEnumerationItems, TCookie]|None):
        super().__init__(enumerator)
        
        self.__cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems] = RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems].__Cookie(self, RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems].__Delegate(self._GetEnumerator, self._GetEnumerationItems, super()._MoveNextOverride))
        self.__moveNext: IRecursiveEnumerationDelegate[TEnumerationItems] = _NullRecursiveEnumerationDelegate[TEnumerationItems]() if delegate is None else delegate
        self.__handler: IRecursiveEnumerationHandlerBase[TEnumerationItems, TCookie] = _NullRecursiveEnumerationHandler[TEnumerationItems, TCookie]() if handler is None else handler
    
    @final
    def _GetCookie(self) -> IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]:
        return self.__cookie
    
    @abstractmethod
    def _GetStackItem(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> TStackItems:
        pass
    @abstractmethod
    def _GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    @abstractmethod
    def _GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        pass

    def _OnStarting(self) -> bool:
        if super()._OnStarting() and self.__handler.OnStartingEnumeration():
            self.__moveNext.Initialize()

            return True
        
        return False
    
    def _OnEnteringLevel(self, item: TEnumerationItems) -> None:
        self.__handler.OnEnteringEnumerationLevel(item)
    def _OnExitingLevel(self, cookie: TCookie) -> None:
        self.__handler.OnExitingEnumerationLevel(cookie)
    
    def _OnEnteringSublevel(self, item: TEnumerationItems) -> bool|None:
        return self.__handler.OnEnteringSubenumerationLevel(item)
    def _OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        return self.__handler.OnExitingSubenumerationLevel(cookie)
    
    def _OnEnteringMainLevel(self, item: TEnumerationItems) -> bool|None:
        return self.__handler.OnEnteringMainEnumerationLevel(item)
    def _OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
        return self.__handler.OnExitingMainEnumerationLevel(cookie)
    
    @final
    def GetCurrent(self) -> TEnumerationItems|None:
        return self.__moveNext.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext.MoveNext()
    
    def _OnEnded(self) -> None:
        self.__moveNext.Dispose()

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        self.__handler.OnStoppedEnumeration()
class RecursiveEnumerator[T](RecursiveEnumeratorBase[T, None, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandlerBase[T, None]|None = None):
        super().__init__(enumerator, _FIFO(self._GetCookie()), handler)
    
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
    def __init__(self, enumerator: IEnumerator[T], enumerationOrder: EnumerationOrder, handler: IRecursiveEnumerationHandlerBase[T, T]|None = None):
        def getDelegate(enumerationOrder: EnumerationOrder, cookie: IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]]) -> IRecursiveEnumerationDelegate[T]|None:
            match enumerationOrder:
                case EnumerationOrder.Null:
                    return None
                case EnumerationOrder.FIFO:
                    return _FIFO(cookie)
                case EnumerationOrder.LIFO:
                    return _LIFO(cookie)
                case _:
                    raise ValueError(enumerationOrder)
        
        super().__init__(enumerator, getDelegate(enumerationOrder, self._GetCookie()), handler)
    
    @final
    def _CreateStack(self) -> Stack[DualResult[T, IEnumerator[T]]]:
        return Stack[DualResult[T, IEnumerator[T]]]()
    
    @final
    def _GetStackItem(self, item: T, enumerator: IEnumerator[T]) -> DualResult[T, IEnumerator[T]]:
        return DualResult[T, IEnumerator[T]](item, enumerator)
    @final
    def _GetStackItemAsEnumerator(self, item: DualResult[T, IEnumerator[T]]) -> IEnumerator[T]:
        return item.GetValue()
    @final
    def _GetStackItemAsCookie(self, item: DualResult[T, IEnumerator[T]]) -> T:
        return item.GetKey()

class RecursivelyEnumerable[T](Enumerable[T], IRecursivelyEnumerable[T]):
    class __IEnumerator(_RecursiveEnumeratorBase[T]):
        def __init__(self):
            super().__init__()
        
        @abstractmethod
        def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
            pass
        
        @final
        def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
            return self._GetEnumerable()._AsRecursivelyEnumerable(enumerationItems)

    class Enumerator(RecursiveEnumerator[T], __IEnumerator[T]):
        def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandlerBase[T, None]|None = None):
            super().__init__(enumerator, handler)

            self.__enumerable: RecursivelyEnumerable[T] = enumerable
        
        @final
        def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
            return self.__enumerable
    class StackedEnumerator(StackedRecursiveEnumerator[T], __IEnumerator[T]):
        def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T], enumerationOrder: EnumerationOrder, handler: IRecursiveEnumerationHandlerBase[T, T]|None = None):
            super().__init__(enumerator, enumerationOrder, handler)

            self.__enumerable: RecursivelyEnumerable[T] = enumerable
        
        @final
        def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
            return self.__enumerable

    @final
    class __Updater(ValueFunctionUpdater[IEnumerable[T]]):
        def __init__(self, enumerable: IRecursivelyEnumerable[T], updater: Method[IFunction[IEnumerable[T]]]):
            super().__init__(updater)

            self.__enumerable: IRecursivelyEnumerable[T] = enumerable
        
        def _GetValue(self) -> IEnumerable[T]:
            return EnumeratorProvider[T](lambda: self.__enumerable.TryGetRecursiveEnumerator())
    
    def __init__(self):
        def update(func: IFunction[IEnumerable[T]]) -> None:
            self.__recursive = func
        
        super().__init__()
    
        self.__recursive: IFunction[IEnumerable[T]] = RecursivelyEnumerable[T].__Updater(self, update)
    
    @abstractmethod
    def _AsRecursivelyEnumerable(self, container: T) -> IEnumerable[T]:
        pass

    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[T]:
        return self.__recursive.GetValue()
    
    def _TryGetRecursiveEnumerator(self, enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandler[T]|None) -> IEnumerator[T]|None:
        return RecursivelyEnumerable[T].Enumerator(self, enumerator, handler)
    def _TryGetRecursiveStackedEnumerator(self, enumerator: IEnumerator[T], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[T]|None) -> IEnumerator[T]|None:
        return None if enumerationOrder == EnumerationOrder.Null else RecursivelyEnumerable[T].StackedEnumerator(self, enumerator, enumerationOrder, handler)

    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        if enumerationOrder == EnumerationOrder.Null:
            return None
        
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        if enumerator is None:
            return None
        
        match enumerationOrder:
            case EnumerationOrder.FIFO:
                return self._TryGetRecursiveEnumerator(enumerator, handler)
            case EnumerationOrder.LIFO:
                return self._TryGetRecursiveStackedEnumerator(enumerator, EnumerationOrder.LIFO, None if handler is None else handler.AsStackHandler())
            case _:
                raise ValueError(enumerationOrder)
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        if enumerationOrder == EnumerationOrder.Null:
            return None
        
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        return None if enumerator is None else self._TryGetRecursiveStackedEnumerator(enumerator, enumerationOrder, handler)