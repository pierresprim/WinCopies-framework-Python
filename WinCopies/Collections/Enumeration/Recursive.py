from abc import abstractmethod
from typing import final



from WinCopies import IInterface, Abstract, NullableBoolean, ToNullableBoolean

from WinCopies.Collections.Enumeration import IEnumerable, SystemIterator, IEnumerator, Enumerable, EnumeratorProvider, AbstractEnumerator, Iterator, GetEnumerator
from WinCopies.Collections.Linked.Singly import Stack

from WinCopies.Typing import InvalidOperationError, INullable
from WinCopies.Typing.Delegate import Converter, Function, Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import DualResult

class IRecursivelyEnumerable[T](IEnumerable[T]):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def TryGetRecursiveEnumerator(self, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        pass
    @final
    def GetRecursiveEnumerator(self, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetRecursiveEnumerator(handler))

    @abstractmethod
    def TryGetRecursiveStackedEnumerator(self, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        pass
    @final
    def GetRecursiveStackedEnumerator(self, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetRecursiveStackedEnumerator(handler))
    
    @abstractmethod
    def AsRecursivelyEnumerable(self) -> IEnumerable[T]:
        pass

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
class IRecursiveStackedEnumerationHandler[T](IRecursiveEnumerationHandlerBase[T, T]):
    def __init__(self):
        super().__init__()

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
    def __init__(self, handler: IRecursiveEnumerationHandler[TOut]):
        super().__init__(handler)
    
    @final
    def OnExitingEnumerationLevel(self, cookie: None) -> None:
        self._GetHandler().OnExitingEnumerationLevel(cookie)
    
    @final
    def OnExitingMainEnumerationLevel(self, cookie: None) -> bool|None:
        return self._GetHandler().OnExitingMainEnumerationLevel(cookie)
    
    @final
    def OnExitingSubenumerationLevel(self, cookie: None) -> bool|None:
        return self._GetHandler().OnExitingSubenumerationLevel(cookie)
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

class _RecursiveEnumeratorBase[T](IEnumerator[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        pass
class RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems](AbstractEnumerator[TEnumerationItems], _RecursiveEnumeratorBase[TEnumerationItems]):
    def __init__(self, enumerator: IEnumerator[TEnumerationItems], handler: IRecursiveEnumerationHandlerBase[TEnumerationItems, TCookie]|None):
        super().__init__(enumerator)
        
        self.__moveNext: Function[bool]|None = None
        self.__first: TStackItems|None = None
        self.__currentEnumerator: IEnumerator[TEnumerationItems]|None = None
        self.__enumerators: Stack[TStackItems]|None = None
        self.__handler: IRecursiveEnumerationHandlerBase[TEnumerationItems, TCookie] = _NullRecursiveEnumerationHandler[TEnumerationItems, TCookie]() if handler is None else handler
    
    @abstractmethod
    def _GetStackItems(self, stackItems: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    
    @abstractmethod
    def _GetStackItem(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> TStackItems:
        pass
    @abstractmethod
    def _GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    @abstractmethod
    def _GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        pass
    
    @final
    def __Push(self, item: TStackItems) -> None:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        self.__enumerators.Push(item)

    @final
    def __TryPeek(self) -> INullable[TStackItems]:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        return self.__enumerators.TryPeek()
    @final
    def __TryPop(self) -> INullable[TStackItems]:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        self.__enumerators.TryPop()

        return self.__enumerators.TryPeek()

    def _OnStarting(self) -> bool:
        if super()._OnStarting() and self.__handler.OnStartingEnumeration():
            self.__enumerators = Stack[TStackItems]()
            self.__moveNext = self.__MoveNext

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
    def __OnEnteringSublevel(self, item: TEnumerationItems) -> bool|None:
        if self._OnEnteringSublevel(item):
            self._OnEnteringLevel(item)

            return True
        
        return False
    @final
    def __OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        if self._OnExitingSublevel(cookie):
            self._OnExitingLevel(cookie)

            return True
        
        return False
    
    @final
    def __OnEnteringMainLevel(self, item: TEnumerationItems) -> bool|None:
        if self._OnEnteringMainLevel(item):
            self._OnEnteringLevel(item)

            return True
        
        return False
    @final
    def __OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
        if self._OnExitingMainLevel(cookie):
            self._OnExitingLevel(cookie)

            return True
        
        return False
    
    @final
    def __MoveNext(self) -> bool:
        def setCurrentEnumerator(value: IEnumerator[TEnumerationItems]) -> None:
            self.__currentEnumerator = value
        
        def moveNext() -> bool:
            def getEnumerator() -> DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]]:
                item: TEnumerationItems = self.__currentEnumerator.GetCurrent() # type: ignore
                iterator: SystemIterator[TEnumerationItems] = iter(self._GetEnumerationItems(item).AsIterable())

                return DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]](item, iterator if isinstance(iterator, IEnumerator) else Iterator[TEnumerationItems](iterator))
            
            def moveNext(enumerator: IEnumerator[TEnumerationItems]) -> bool:
                return enumerator.MoveNext()
            
            def tryEnterLevel() -> NullableBoolean:
                def processEnumerator(currentItem: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> NullableBoolean:
                    while enumerator.MoveNext():
                        result: bool|None = self.__OnEnteringSublevel(currentItem)
                        
                        if result is None:
                            return NullableBoolean.Null
                        
                        if result is True:
                            self.__Push(self._GetStackItem(currentItem, enumerator))

                            setCurrentEnumerator(enumerator)
                            
                            return NullableBoolean.BoolTrue
                    
                    return NullableBoolean.BoolFalse
                
                result: DualResult[TEnumerationItems, IEnumerator[TEnumerationItems]] = getEnumerator()
                
                return processEnumerator(result.GetKey(), result.GetValue())
            
            def loop() -> bool|None:
                nonlocal result

                enumerator: IEnumerator[TEnumerationItems]|None = None
                
                def loop(result: TStackItems) -> bool|None:
                    nonlocal enumerator

                    match ToNullableBoolean(self.__OnExitingSublevel(self._GetStackItemAsCookie(result))):
                        case NullableBoolean.BoolTrue:
                            if moveNext(enumerator := self._GetStackItemAsEnumerator(result)):
                                setCurrentEnumerator(enumerator)

                                return True
                        
                        case NullableBoolean.Null:
                            return False
                        
                        case _:
                            return None
                    
                    return None
                
                result = self.__TryPop()
                loopResult: bool|None = None

                while result.HasValue():
                    if (loopResult := loop(result.GetValue())) is not None:
                        return loopResult
                    
                    result = self.__TryPop()
                
                return None

            match tryEnterLevel():
                case NullableBoolean.BoolTrue:
                    return True
                case NullableBoolean.Null:
                    return False
                case _:
                    pass
            
            result: INullable[TStackItems] = self.__TryPeek()

            if result.HasValue():
                if moveNext(self._GetStackItems(result.GetValue())):
                    return True
                
                loopResult: bool|None = loop()

                if loopResult is not None:
                    return loopResult
        
            self.__OnExitingMainLevel(self._GetStackItemAsCookie(self.__first)) # type: ignore

            self.__moveNext = self.__MoveNext

            return self.__moveNext()
        
        current: TEnumerationItems|None = None

        while super()._MoveNextOverride():
            setCurrentEnumerator(self._GetEnumerator())

            match ToNullableBoolean(self.__OnEnteringMainLevel(current := self.__currentEnumerator.GetCurrent(), self.__currentEnumerator)): # type: ignore
                case NullableBoolean.BoolTrue:
                    self.__first = self._GetStackItemAsCookie(self._GetStackItem(current, self.__currentEnumerator)) # type: ignore
                    
                    self.__moveNext = moveNext

                    return True
                
                case NullableBoolean.Null:
                    return False
                
                case _:
                    continue
        
        return False
    
    @final
    def GetCurrent(self) -> TEnumerationItems|None:
        return None if self.__currentEnumerator is None else self.__currentEnumerator.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return False if self.__moveNext is None else self.__moveNext()
    
    def _OnEnded(self) -> None:
        self.__currentEnumerator = None
        self.__first = None

        if self.__enumerators is not None:
            self.__enumerators.Clear()
            self.__enumerators = None

        self.__moveNext = None

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        self.__handler.OnStoppedEnumeration()
class RecursiveEnumerator[T](RecursiveEnumeratorBase[T, None, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandlerBase[T, None]|None = None):
        super().__init__(enumerator, handler)
    
    @final
    def _GetStackItems(self, stackItems: IEnumerator[T]) -> IEnumerator[T]:
        return stackItems
    
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
    def __init__(self, enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandlerBase[T, T]|None = None):
        super().__init__(enumerator, handler)
    
    @final
    def _GetStackItems(self, stackItems: DualResult[T, IEnumerator[T]]) -> IEnumerator[T]:
        return stackItems.GetValue()
    
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
        def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T], handler: IRecursiveEnumerationHandlerBase[T, T]|None = None):
            super().__init__(enumerator, handler)

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
    def _TryGetRecursiveStackedEnumerator(self, enumerator: IEnumerator[T], handler: IRecursiveStackedEnumerationHandler[T]|None) -> IEnumerator[T]|None:
        return RecursivelyEnumerable[T].StackedEnumerator(self, enumerator, handler)

    def TryGetRecursiveEnumerator(self, handler: IRecursiveEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        return None if enumerator is None else self._TryGetRecursiveEnumerator(enumerator, handler)
    def TryGetRecursiveStackedEnumerator(self, handler: IRecursiveStackedEnumerationHandler[T]|None = None) -> IEnumerator[T]|None:
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        return None if enumerator is None else self._TryGetRecursiveStackedEnumerator(enumerator, handler)