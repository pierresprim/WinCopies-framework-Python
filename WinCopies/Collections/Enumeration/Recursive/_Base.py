from __future__ import annotations

from abc import abstractmethod
from typing import final



from WinCopies import IInterface, Abstract, NullableBoolean, ToNullableBoolean

from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator
from WinCopies.Collections.Enumeration.Recursive.Base import IRecursiveEnumerationHandlerBase, IRecursiveEnumerationDelegate, IRecursiveEnumerationCookie

from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import Converter, Function
from WinCopies.Typing.Pairing import DualResult

@final
class NullRecursiveEnumerationDelegate[T](Abstract, IRecursiveEnumerationDelegate[T]):
    def __init__(self) -> None:
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
class RecursiveEnumerationDelegate[TEnumerationItems, TCookie, TStackItems](Abstract, IRecursiveEnumerationDelegate[TEnumerationItems]):
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
    def _OnExitingLevel(self, enumerator: IEnumerator[TEnumerationItems]) -> None:
        pass
    
    @final
    def __ProcessEnumerator(self, currentItem: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems], cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> NullableBoolean:
        while enumerator.MoveNext():
            result: bool|None = cookie.OnEnteringSublevel(currentItem)
            
            if result is None:
                return NullableBoolean.Null
            
            if result is True:
                self._OnEnteringLevel(currentItem, enumerator)
                
                return NullableBoolean.BoolTrue
        
        return NullableBoolean.BoolFalse
    
    @final
    def _TryEnterLevel(self) -> NullableBoolean:
        def getEnumerator(cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]]|None:
            enumerator: IEnumerator[TEnumerationItems]|None = self._GetCurrentEnumerator()

            if enumerator is None:
                return None
            
            item: TEnumerationItems|None = enumerator.GetCurrent()

            return None if item is None else DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]](item, cookie.GetEnumerationItems(item).GetEnumerator())
        
        cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems] = self._GetCookie()
        result: DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]]|None = getEnumerator(cookie)

        return NullableBoolean.BoolFalse if result is None else self.__ProcessEnumerator(result.GetKey(), result.GetValue(), cookie)
    
    def _Loop(self, result: INullable[TStackItems]) -> bool|None:
        def moveNext(enumerator: IEnumerator[TEnumerationItems]) -> bool:
            return enumerator.MoveNext()
        
        def tryPop(cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> INullable[TStackItems]:
            return cookie.TryPop()
        
        def loop(cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> bool|None:
            nonlocal result

            if (loopResult := cookie.OnExitingSublevel(cookie.GetStackItemAsCookie(result.GetValue()))) is None:
                return False
            
            while (result := tryPop(cookie)).HasValue():
                if loopResult is True and moveNext(enumerator := cookie.GetStackItemAsEnumerator(result.GetValue())):
                    self._OnExitingLevel(enumerator)

                    return True

                if (loopResult := cookie.OnExitingSublevel(cookie.GetStackItemAsCookie(result.GetValue()))) is None:
                    return False
            
            return None
        
        cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems] = self._GetCookie()
        loopResult: bool|None = cookie.OnExitingSublevel(cookie.GetStackItemAsCookie(result.GetValue()))
        
        if loopResult is None:
            return False
        
        enumerator: IEnumerator[TEnumerationItems]|None = None
        
        if loopResult is False:
            if (result := tryPop(cookie)).HasValue():
                return loop(cookie)
        
        if (result := tryPop(cookie)).HasValue():
            if moveNext(enumerator := cookie.GetStackItemAsEnumerator(result.GetValue())):
                self._OnExitingLevel(enumerator)

                return True
            
            return loop(cookie)
        
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
class FIFO[TEnumerationItems, TCookie, TStackItems](RecursiveEnumerationDelegate[TEnumerationItems, TCookie, TStackItems]):
    def __init__(self, cookieProvider: Function[IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]]) -> None:
        super().__init__(cookieProvider)
        
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
        
        def moveNext(current: TEnumerationItems, currentEnumerator: IEnumerator[TEnumerationItems]|None, cookie: IRecursiveEnumerationCookie[TEnumerationItems, TCookie, TStackItems]) -> bool:
            def moveNext() -> bool:
                match self._TryEnterLevel():
                    case NullableBoolean.BoolTrue:
                        return True
                    case NullableBoolean.Null:
                        return False
                    case _:
                        pass
                
                result: INullable[TStackItems] = cookie.TryPeek()

                if result.HasValue():
                    if cookie.GetStackItemAsEnumerator(result.GetValue()).MoveNext():
                        return True
                    
                    loopResult: bool|None = self._Loop(result)

                    if loopResult is not None:
                        return loopResult
            
                first: TStackItems|None = self.__first

                if first is not None:
                    cookie.OnExitingMainLevel(cookie.GetStackItemAsCookie(first))

                self._UpdateMoveNext(self._MoveNext)

                return self._MoveNext()
            
            if currentEnumerator is None:
                return False
            
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
                    if moveNext(current, currentEnumerator, cookie):
                        return True
                    
                    continue
                
                case NullableBoolean.Null:
                    return False
                
                case _:
                    continue
        
        return False
    
    def Dispose(self) -> None:
        super().Dispose()

        self.__first = None
@final
class LIFO[T](RecursiveEnumerationDelegate[T, T, DualResult[T, IEnumerator[T]]]):
    def __init__(self, cookieProvider: Function[IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]]]) -> None:
        super().__init__(cookieProvider)
        
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
        
        def moveNext(current: T, currentEnumerator: IEnumerator[T]|None, cookie: IRecursiveEnumerationCookie[T, T, DualResult[T, IEnumerator[T]]]) -> bool|None:
            def moveNext() -> bool:
                def _tryEnterLevel() -> bool|None:
                    _result: NullableBoolean = tryEnterLevel()

                    match _result:
                        case NullableBoolean.BoolTrue:
                            while _result == NullableBoolean.BoolTrue:
                                _result = tryEnterLevel()
                            
                            if _result == NullableBoolean.Null:
                                return False
                            
                            self._SetCurrentEnumerator(getEnumerator(cookie.TryPeek()))
                        case NullableBoolean.Null:
                            return False
                        case _:
                            return None

                    return True
                
                result: INullable[DualResult[T, IEnumerator[T]]] = cookie.TryPeek()

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
                    cookie.OnExitingMainLevel(cookie.GetStackItemAsCookie(first))

                self._UpdateMoveNext(self._MoveNext)

                return self._MoveNext()
            
            if currentEnumerator is None:
                return None
            
            self.__first = cookie.GetStackItem(current, currentEnumerator)

            result: NullableBoolean = tryEnterLevel()

            match result:
                case NullableBoolean.BoolTrue:
                    while result == NullableBoolean.BoolTrue:
                        result = tryEnterLevel()
                    
                    if result == NullableBoolean.Null:
                        return False
                    
                    self._SetCurrentEnumerator(getEnumerator(cookie.TryPeek()))
                
                    self._UpdateMoveNext(moveNext)
                case NullableBoolean.Null:
                    return False
                case _:
                    pass
            
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

                    if result is None:
                        continue

                    return result
                
                case NullableBoolean.Null:
                    return False
                
                case _:
                    continue
        
        return False
    
    def Dispose(self) -> None:
        super().Dispose()

        self.__first = None

class IRecursiveEnumeratorAbstract[T](IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        pass
class IRecursiveEnumeratorBase[T, TCookie, TStackItems](IRecursiveEnumeratorAbstract[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetCookie(self) -> IRecursiveEnumerationCookie[T, TCookie, TStackItems]:
        pass

class IDelegate[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetEnumerator(self) -> IEnumerator[T]:
        pass

    @abstractmethod
    def GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        pass

    @abstractmethod
    def MoveNext(self) -> bool:
        pass
@final
class Delegate[T](Abstract, IDelegate[T]):
    def __init__(self, enumeratorProvider: Function[IEnumerator[T]], enumerationItemsProvider: Converter[T, IEnumerable[T]], moveNextAction: Function[bool]) -> None:
        super().__init__()

        self.__enumeratorProvider: Function[IEnumerator[T]] = enumeratorProvider
        self.__enumerationItemsProvider: Converter[T, IEnumerable[T]] = enumerationItemsProvider
        self.__moveNextAction: Function[bool] = moveNextAction
    
    def GetEnumerator(self) -> IEnumerator[T]:
        return self.__enumeratorProvider()

    def GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        return self.__enumerationItemsProvider(enumerationItems)
    
    def MoveNext(self) -> bool:
        return self.__moveNextAction()

@final
class NullRecursiveEnumerationHandler[TItem, TCookie](Abstract, IRecursiveEnumerationHandlerBase[TItem, TCookie]):
    def __init__(self) -> None:
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