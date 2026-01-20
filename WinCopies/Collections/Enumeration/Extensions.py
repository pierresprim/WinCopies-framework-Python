# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 02:12:00 2025

@author: Pierre Sprimont
"""

from abc import abstractmethod
from typing import final



from WinCopies import IInterface, Abstract

from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, Enumerable, EnumeratorBase, AbstractionEnumerator, GetEmptyEnumerable
from WinCopies.Collections.Linked.Doubly import IList, List, IDoublyLinkedNode

from WinCopies.Delegates import BoolFalse

from WinCopies.Typing.Delegate import Converter, Function, NullableFunction
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class _ICookie[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def SetIterable(self, iterable: IEnumerable[T]) -> None:
        pass
    @abstractmethod
    def UnsetIterable(self) -> None:
        pass

class _IToken[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> T|None:
        pass
    
    @abstractmethod
    def MoveNext(self) -> bool:
        pass
@final
class _NullToken[T](Abstract, _IToken[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def GetCurrent(self) -> T|None:
        return None
    
    def MoveNext(self) -> bool:
        return False
@final
class _Token[T](Abstract, _IToken[T]):
    def __init__(self, node: IDoublyLinkedNode[T]) -> None:
        self.__node: IDoublyLinkedNode[T]|None = None
        self.__moveNext: Function[bool] = BoolFalse

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

        self.__node = node
        self.__moveNext = moveNext
    
    def GetCurrent(self) -> T|None:
        return None if self.__node is None else self.__node.GetValue()
    
    def MoveNext(self) -> bool:
        return self.__moveNext()

@final
class _AbstractEnumerator[T](Abstract):
    def __init__(self, enumerator: _AbstractionEnumerator[T]) -> None:
        super().__init__()

        self.__enumerator: _AbstractionEnumerator[T] = enumerator
    
    def GetFirst(self) -> _IToken[T]|None:
        return self.__enumerator.GetFirst()
    
    def GetCurrent(self) -> _IToken[T]|None:
        return self.__enumerator.GetToken()
    
    def MoveNext(self) -> bool:
        return self.__enumerator.MoveNext()

@final
class _Enumerator[T](EnumeratorBase[T]):
    def __init__(self, enumerator: _AbstractEnumerator[T], token: _IToken[T]) -> None:
        super().__init__()

        self.__enumerator: _AbstractEnumerator[T] = enumerator
        self.__token: _IToken[T] = token
    
    @staticmethod
    def TryCreate(enumerator: _AbstractionEnumerator[T]) -> _Enumerator[T]|None:
        first: _IToken[T]|None = enumerator.GetFirst()

        return None if first is None else _Enumerator[T](_AbstractEnumerator[T](enumerator), first)
    
    def IsResetSupported(self) -> bool:
        return True
    
    def GetCurrent(self) -> T|None:
        return self.__token.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        if self.__token.MoveNext():
            return True
        
        if self.__enumerator.MoveNext():
            token: _IToken[T]|None = self.__enumerator.GetCurrent()

            if token is None:
                return False

            self.__token = token

            return True
        
        return False
    
    def _OnStopped(self) -> None:
        self.__token = _NullToken[T]()
    
    def _ResetOverride(self) -> bool:
        token: _IToken[T]|None = self.__enumerator.GetFirst()

        if token is not None:
            self.__token = token

        return True

@final
class _AbstractionEnumerator[T](AbstractionEnumerator[T, T]):
    def __init__(self, builder: _ICookie[T], enumerator: IEnumerator[T]) -> None:
        super().__init__(enumerator)

        self.__builder: _ICookie[T] = builder
        self.__items: IList[T]|None = None
        self.__getEnumerator: NullableFunction[IEnumerator[T]]|None = None
    
    def __GetEnumerator(self) -> IEnumerator[T]:
        self.__getEnumerator = lambda: _Enumerator[T].TryCreate(self)

        return self
    
    def GetItemEnumerator(self) -> IEnumerator[T]|None:
        getEnumerator: NullableFunction[IEnumerator[T]]|None = self.__getEnumerator

        return None if getEnumerator is None else getEnumerator()
    
    def GetCurrent(self) -> T|None:
        items: IList[T]|None = self.__items

        return None if items is None else items.TryGetLastValueOrNone()
    
    def __GetToken(self, func: Converter[IList[T], IDoublyLinkedNode[T]|None]) -> _IToken[T]|None:
        items: IList[T]|None = self.__items

        if items is None:
            return None
        
        node: IDoublyLinkedNode[T]|None = func(items)

        return None if node is None else _Token[T](node)
    
    def GetFirst(self) -> _IToken[T]|None:
        return self.__GetToken(lambda items: items.GetFirst())
    def GetToken(self) -> _IToken[T]|None:
        return self.__GetToken(lambda items: items.GetLast())
    
    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__getEnumerator = self.__GetEnumerator
            self.__items = List[T]()

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        def moveNext() -> bool:
            value: T|None = self.GetCurrent()

            if value is None:
                self.__builder.UnsetIterable()

                return False

            items: IList[T]|None = self.__items

            if items is None:
                return False
            
            items.AddLast(value)

            return True
        
        if super()._MoveNextOverride():
            return moveNext()
        
        items: IList[T]|None = self.__items

        if items is not None:
            self.__builder.SetIterable(items)
        
        return False
    
    def _OnEnded(self) -> None:
        self.__items = None
        self.__getEnumerator = None

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass
    
    def _ResetOverride(self) -> bool:
        return True

@final
class _ItemEnumerable[T](Enumerable[T]):
    def __init__(self, builder: _ICookie[T], enumerator: IEnumerator[T]) -> None:
        super().__init__()

        self.__enumerator: _AbstractionEnumerator[T] = _AbstractionEnumerator[T](builder, enumerator)
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self.__enumerator.GetItemEnumerator()

@final
class _Enumerable[T](Enumerable[T]):
    def __init__(self, builder: _ICookie[T], iterable: IEnumerable[T]) -> None:
        super().__init__()

        self.__builder: _ICookie[T] = builder
        self.__iterable: IEnumerable[T] = iterable
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        enumerator: IEnumerator[T]|None = self.__iterable.TryGetEnumerator()

        if enumerator is None:
            self.__builder.UnsetIterable()

            return None
        
        iterable: IEnumerable[T] = _ItemEnumerable[T](self.__builder, enumerator)

        self.__builder.SetIterable(iterable)

        return iterable.TryGetEnumerator()

class IterableBuilder[T](Enumerable[T]):
    @final
    class _Cookie[_T](Abstract, _ICookie[_T]):
        def __init__(self, builder: IterableBuilder[_T]) -> None:
            super().__init__()

            self.__builder: IterableBuilder[_T] = builder
        
        def SetIterable(self, iterable: IEnumerable[_T]) -> None:
            return self.__builder._SetIterable(iterable)
        def UnsetIterable(self) -> None:
            return self.__builder._UnsetIterable()
    
    def __init__(self, iterable: IEnumerable[T]) -> None:
        super().__init__()

        self.__iterable: IEnumerable[T] = _Enumerable[T](IterableBuilder[T]._Cookie(self), iterable)
    
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

        self.__SetIterable(GetEmptyEnumerable())
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self.__iterable.TryGetEnumerator()