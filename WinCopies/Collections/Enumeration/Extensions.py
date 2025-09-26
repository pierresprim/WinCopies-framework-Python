# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 02:12:00 2025

@author: Pierre Sprimont
"""

from __future__ import annotations

from abc import abstractmethod
from typing import final



from WinCopies import IInterface, NullableBoolean, ToNullableBoolean

from WinCopies.Collections.Enumeration import IEnumerable, SystemIterable, SystemIterator, IEnumerator, Enumerable, EnumeratorBase, IteratorProvider, AbstractEnumerator, AbstractionEnumerator, Iterator, GetEnumerator, GetNullEnumerable, GetIterator
from WinCopies.Collections.Linked.Singly import Stack
from WinCopies.Collections.Linked.Doubly import IList, List, IDoublyLinkedNode

from WinCopies.Typing import InvalidOperationError, INullable
from WinCopies.Typing.Delegate import Converter, Function
from WinCopies.Typing.Pairing import DualResult
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class _RecursiveEnumeratorBase[T](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetEnumerationItems(self, enumerationItems: T) -> IEnumerable[T]:
        pass
class RecursiveEnumeratorBase[TEnumerationItems, TCookie, TStackItems](AbstractEnumerator[TEnumerationItems], _RecursiveEnumeratorBase[TEnumerationItems]):
    def __init__(self, enumerator: IEnumerator[TEnumerationItems]):
        super().__init__(enumerator)
        
        self.__moveNext: Function[bool]|None = None
        self.__first: TStackItems|None = None
        self.__currentEnumerator: IEnumerator[TEnumerationItems]|None = None
        self.__enumerators: Stack[TStackItems]|None = None
    
    @abstractmethod
    def _GetStackItems(self, stackItems: TStackItems) -> IEnumerator[TEnumerationItems]:
        pass
    
    @abstractmethod
    def _CreateStack(self) -> Stack[TStackItems]:
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
    def _Push(self, item: TStackItems) -> None:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        self.__enumerators.Push(item)

    @final
    def _TryPeek(self) -> INullable[TStackItems]:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        return self.__enumerators.TryPeek()
    @final
    def _TryPop(self) -> INullable[TStackItems]:
        if self.__enumerators is None:
            raise InvalidOperationError()
        
        self.__enumerators.TryPop()

        return self._TryPeek()

    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__enumerators = self._CreateStack()
            self.__moveNext = self.__MoveNext

            return True
        
        return False
    
    def _OnEnteringLevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> None:
        pass
    def _OnExitingLevel(self, cookie: TCookie) -> None:
        pass
    
    def _OnEnteringSublevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> bool|None:
        return True
    def _OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        return True
    
    def _OnEnteringMainLevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> bool|None:
        return True
    def _OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
        return True
    
    @final
    def __OnEnteringSublevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> bool|None:
        if self._OnEnteringSublevel(item, enumerator):
            self._OnEnteringLevel(item, enumerator)

            return True
        
        return False
    @final
    def __OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        if self._OnExitingSublevel(cookie):
            self._OnExitingLevel(cookie)

            return True
        
        return False
    
    @final
    def __OnEnteringMainLevel(self, item: TEnumerationItems, enumerator: IEnumerator[TEnumerationItems]) -> bool|None:
        if self._OnEnteringMainLevel(item, enumerator):
            self._OnEnteringLevel(item, enumerator)

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
                        result: bool|None = self.__OnEnteringSublevel(currentItem, enumerator)
                        
                        if result is None:
                            return NullableBoolean.Null
                        
                        if result is True:
                            self._Push(self._GetStackItem(currentItem, enumerator))

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
                
                result = self._TryPop()
                loopResult: bool|None = None

                while result.HasValue():
                    if (loopResult := loop(result.GetValue())) is not None:
                        return loopResult
                    
                    result = self._TryPop()
                
                return None

            match tryEnterLevel():
                case NullableBoolean.BoolTrue:
                    return True
                case NullableBoolean.Null:
                    return False
                case _:
                    pass
            
            result: INullable[TStackItems] = self._TryPeek()

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
        pass
class RecursiveEnumerator[T](RecursiveEnumeratorBase[T, None, IEnumerator[T]]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    @final
    def _GetStackItems(self, stackItems: IEnumerator[T]) -> IEnumerator[T]:
        return stackItems
    
    @final
    def _CreateStack(self) -> Stack[IEnumerator[T]]:
        return Stack[IEnumerator[T]]()
    
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
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
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

class IRecursivelyEnumerable[T](IEnumerable[T]):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def TryGetRecursiveEnumerator(self) -> IEnumerator[T]|None:
        pass
    @final
    def GetRecursiveEnumerator(self) -> IEnumerator[T]:
        return GetEnumerator(self.TryGetRecursiveEnumerator())
    
    @abstractmethod
    def AsRecursivelyIterable(self) -> SystemIterable[T]:
        pass

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
        def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T]):
            super().__init__(enumerator)

            self.__enumerable: RecursivelyEnumerable[T] = enumerable
        
        @final
        def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
            return self.__enumerable
    class StackedEnumerator(StackedRecursiveEnumerator[T], __IEnumerator[T]):
        def __init__(self, enumerable: RecursivelyEnumerable[T], enumerator: IEnumerator[T]):
            super().__init__(enumerator)

            self.__enumerable: RecursivelyEnumerable[T] = enumerable
        
        @final
        def _GetEnumerable(self) -> RecursivelyEnumerable[T]:
            return self.__enumerable
    
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _AsRecursivelyEnumerable(self, container: T) -> IEnumerable[T]:
        pass

    @final
    def AsRecursivelyIterable(self) -> SystemIterable[T]:
        return IteratorProvider[T](lambda: GetIterator(self.TryGetRecursiveEnumerator())) # type: ignore
    
    def _TryGetRecursiveEnumerator(self, enumerator: IEnumerator[T]) -> IEnumerator[T]|None:
        return RecursivelyEnumerable[T].Enumerator(self, enumerator)

    def TryGetRecursiveEnumerator(self) -> IEnumerator[T]|None:
        enumerator: IEnumerator[T]|None = self.TryGetEnumerator()

        return None if enumerator is None else self._TryGetRecursiveEnumerator(enumerator)

class IterableBuilder[T](Enumerable[T]):
    @final
    class __Iterable(Enumerable[T]):
        @final
        class __Iterable(Enumerable[T]):
            @final
            class __Enumerator(AbstractionEnumerator[T, T]):
                @final
                class __Enumerator(EnumeratorBase[T]):
                    class IToken(IInterface):
                        def __init__(self):
                            super().__init__()
                        
                        @abstractmethod
                        def GetCurrent(self) -> T|None:
                            pass
                        
                        @abstractmethod
                        def MoveNext(self) -> bool:
                            pass
                    @final
                    class __NullToken(IToken):
                        def __init__(self):
                            super().__init__()
                        
                        def GetCurrent(self) -> T|None:
                            return None
                        
                        def MoveNext(self) -> bool:
                            return False
                    @final
                    class Token(IToken):
                        def __init__(self, node: IDoublyLinkedNode[T]):
                            def moveNext() -> bool:
                                def moveNext() -> bool:
                                    if self.__node is None:
                                        return False
                                    
                                    else:
                                        self.__node = self.__node.GetNext()

                                        return self.__node is not None
                                
                                self.__moveNext = moveNext

                                return True

                            super().__init__()

                            self.__node: IDoublyLinkedNode[T]|None = node
                            self.__moveNext: Function[bool] = moveNext
                        
                        def GetCurrent(self) -> T|None:
                            return None if self.__node is None else self.__node.GetValue()
                        
                        def MoveNext(self) -> bool:
                            return self.__moveNext()
                    
                    @final
                    class __Enumerator(IInterface):
                        def __init__(self, enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator):
                            super().__init__()

                            self.__enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator = enumerator
                        
                        def GetFirst(self) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken:
                            return self.__enumerator.GetFirst() # type: ignore
                        
                        def GetCurrent(self) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken:
                            return self.__enumerator.GetToken() # type: ignore
                        
                        def MoveNext(self) -> bool:
                            return self.__enumerator.MoveNext()
                    
                    def __init__(self, enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator):
                        super().__init__()

                        self.__enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.__Enumerator = IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.__Enumerator(enumerator)
                        self.__token: IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken = enumerator.GetFirst() # type: ignore
                    
                    def IsResetSupported(self) -> bool:
                        return True
                    
                    def GetCurrent(self) -> T|None:
                        return self.__token.GetCurrent()
                    
                    def _MoveNextOverride(self) -> bool:
                        if self.__token.MoveNext():
                            return True
                        
                        if self.__enumerator.MoveNext():
                            self.__token = self.__enumerator.GetCurrent()

                            return True
                        
                        return False
                    
                    def _OnStopped(self) -> None:
                        self.__token = IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.__NullToken()
                    
                    def _ResetOverride(self) -> bool:
                        self.__token = self.__enumerator.GetFirst()

                        return True
                
                def __init__(self, builder: IterableBuilder[T], enumerator: IEnumerator[T]):
                    super().__init__(enumerator)

                    self.__builder: IterableBuilder[T] = builder
                    self.__items: IList[T] = None # type: ignore
                    self.__getEnumerator: Function[IEnumerator[T]] = None # type: ignore
                
                def __GetEnumerator(self) -> IEnumerator[T]:
                    self.__getEnumerator = lambda: IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator(self)

                    return self
                
                def GetItemEnumerator(self) -> IEnumerator[T]:
                    return self.__getEnumerator()
                
                def GetCurrent(self) -> T|None:
                    return self.__items.TryGetLastValueOrNone()
                
                def __GetToken(self, func: Converter[IList[T], IDoublyLinkedNode[T]|None]) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken|None:
                    node: IDoublyLinkedNode[T]|None = func(self.__items)

                    return None if node is None else IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.Token(node)
                
                def GetFirst(self) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken|None:
                    return self.__GetToken(lambda items: items.GetFirst())
                def GetToken(self) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken|None:
                    return self.__GetToken(lambda items: items.GetLast())
                
                def _OnStarting(self) -> bool:
                    if super()._OnStarting():
                        self.__getEnumerator = self.__GetEnumerator
                        self.__items: IList[T] = List[T]()

                        return True
                    
                    return False
                
                def _MoveNextOverride(self) -> bool:
                    if super()._MoveNextOverride():
                        value: T|None = self.GetCurrent()

                        if value is None:
                            self.__builder._UnsetIterable()

                            return False

                        self.__items.AddLast(value)

                        return True
                    
                    self.__builder._SetIterable(self.__items)
                    
                    return False
                
                def _OnEnded(self) -> None:
                    self.__items = None # type: ignore
                    self.__getEnumerator = None # type: ignore

                    super()._OnEnded()
                
                def _OnStopped(self) -> None:
                    pass
                
                def _ResetOverride(self) -> bool:
                    return True
            
            def __init__(self, builder: IterableBuilder[T], enumerator: IEnumerator[T]):
                super().__init__()

                self.__enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator = IterableBuilder[T].__Iterable.__Iterable.__Enumerator(builder, enumerator)
            
            def TryGetEnumerator(self) -> IEnumerator[T]|None:
                return self.__enumerator.GetItemEnumerator()
        
        def __init__(self, builder: IterableBuilder[T], iterable: IEnumerable[T]):
            super().__init__()

            self.__builder: IterableBuilder[T] = builder
            self.__iterable: IEnumerable[T] = iterable
        
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            enumerator: IEnumerator[T]|None = self.__iterable.TryGetEnumerator()

            if enumerator is None:
                self.__builder._UnsetIterable()

                return None
            
            iterable: IEnumerable[T] = IterableBuilder[T].__Iterable.__Iterable(self.__builder, enumerator)

            self.__builder._SetIterable(iterable)

            return iterable.TryGetEnumerator()
    
    def __init__(self, iterable: IEnumerable[T]):
        super().__init__()

        self.__iterable: IEnumerable[T] = IterableBuilder[T].__Iterable(self, iterable)
    
    @final
    def __SetIterable(self, iterable: IEnumerable[T]) -> None:
        self.__iterable = iterable
    
    @final
    def _SetIterable(self, iterable: IEnumerable[T]) -> None:
        EnsureDirectModuleCall()

        self.__SetIterable(iterable)
    @final
    def _UnsetIterable(self) -> None:
        EnsureDirectModuleCall()

        self.__SetIterable(GetNullEnumerable())
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self.__iterable.TryGetEnumerator()