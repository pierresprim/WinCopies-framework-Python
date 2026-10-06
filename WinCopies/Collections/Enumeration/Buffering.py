from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final



from WinCopies import IInterface, Abstract

from WinCopies.Collections.Enumeration import GetIterationInactiveError
from WinCopies.Collections.Enumeration.Abstraction import AbstractionEnumerator
from WinCopies.Collections.Enumeration.Core import IEnumerable, IEnumerator, Enumerable, EnumeratorBase, GetEmptyEnumerable, GetEmptyEnumerator, AsEnumerable
from WinCopies.Collections.Linked.Doubly.Welded import IList, List, IDoublyLinkedNode

from WinCopies.Delegates import BoolFalse

from WinCopies.Typing.Delegate import Action, Method, Function

class _ICookie[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def SetIterable(self, iterable: IEnumerable[T]) -> None:
        ...
    @abstractmethod
    def UnsetIterable(self) -> None:
        ...

class _IToken[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetCurrent(self) -> T:
        ...
    
    @abstractmethod
    def MoveNext(self) -> bool:
        ...
@final
class _NullToken[T](Abstract, _IToken[T]):
    def __init__(self) -> None: super().__init__()
    
    def GetCurrent(self) -> T: raise GetIterationInactiveError()
    
    def MoveNext(self) -> bool: return False
@final
class _Token[T](Abstract, _IToken[T]):
    def __init__(self, node: IDoublyLinkedNode[T], first: bool) -> None:
        self.__node: IDoublyLinkedNode[T]|None = None
        self.__moveNext: Function[bool] = BoolFalse

        def moveNext() -> bool:
            def moveNext() -> bool:
                node: IDoublyLinkedNode[T]|None = self.__node

                if node is None: return False
                
                self.__node = (node := node.GetNext())

                return node is not None
            
            self.__moveNext = moveNext

            return first

        super().__init__()

        self.__node = node
        self.__moveNext = moveNext
    
    def GetCurrent(self) -> T:
        node: IDoublyLinkedNode[T]|None = self.__node

        if node is None: raise GetIterationInactiveError()
        
        return node.GetValue()
    
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
    def TryCreate(enumerator: _AbstractionEnumerator[T]) -> IEnumerator[T]:
        first: _IToken[T]|None = enumerator.GetFirst()

        return enumerator if first is None else _Enumerator[T](_AbstractEnumerator[T](enumerator), first)
    
    def IsResetSupported(self) -> bool: return True
    
    def _GetCurrent(self) -> T: return self.__token.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        if self.__token.MoveNext(): return True
        
        if self.__enumerator.MoveNext():
            token: _IToken[T]|None = self.__enumerator.GetCurrent()

            if token is None: return False

            self.__token = token

            return True
        
        return False
    
    def _OnEnded(self) -> None: self.__token = _NullToken[T]()
    
    def _ResetOverride(self) -> bool:
        token: _IToken[T]|None = self.__enumerator.GetFirst()

        if token is not None: self.__token = token

        return True

@final
class _AbstractionEnumerator[T](AbstractionEnumerator[T, T]):
    def __init__(self, builder: _ICookie[T], enumerator: IEnumerator[T]) -> None:
        super().__init__(enumerator)

        self.__builder: _ICookie[T] = builder
        self.__items: IList[T]|None = None
        self.__getEnumerator: Function[IEnumerator[T]] = self.__GetEnumerator
    
    def __GetEnumerator(self) -> IEnumerator[T]:
        self.__getEnumerator = lambda: _Enumerator[T].TryCreate(self)

        return self
    
    def GetItemEnumerator(self) -> IEnumerator[T]:
        return self.__getEnumerator()
    
    def _GetCurrent(self) -> T:
        items: IList[T]|None = self.__items

        if items is None: raise GetIterationInactiveError()

        return items.GetLastValue()
    
    def __GetToken(self, first: bool) -> _IToken[T]|None:
        items: IList[T]|None = self.__items

        if items is None: return None
        
        node: IDoublyLinkedNode[T]|None = items.GetFirst() if first else items.GetLast()

        return None if node is None else _Token[T](node, first)
    
    def GetFirst(self) -> _IToken[T]|None:
        return self.__GetToken(True)
    def GetToken(self) -> _IToken[T]|None:
        return self.__GetToken(False)
    
    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__items = List[T]()

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        def moveNext() -> bool:
            value: T = self._GetContainer().GetCurrent()
            items: IList[T]|None = self.__items

            if items is None: return False
            
            items.AddLast(value)

            return True
        
        if super()._MoveNextOverride(): return moveNext()
        
        items: IList[T]|None = self.__items

        if items is not None: self.__builder.SetIterable(items)
        
        return False
    
    def _OnEnded(self) -> None:
        self.__items = None
        self.__getEnumerator = lambda: GetEmptyEnumerator()

        super()._OnEnded()
    
    def _ResetOverride(self) -> bool: return True

@final
class _ItemEnumerable[T](Enumerable[T]):
    def __init__(self, builder: _ICookie[T], enumerator: IEnumerator[T]) -> None:
        super().__init__()

        self.__enumerator: _AbstractionEnumerator[T] = _AbstractionEnumerator[T](builder, enumerator)

    @final
    def IsResumable(self) -> bool|None: return None
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__enumerator.GetItemEnumerator()

@final
class _Enumerable[T](Enumerable[T]):
    def __init__(self, builder: _ICookie[T], iterable: IEnumerable[T]) -> None:
        super().__init__()

        self.__builder: _ICookie[T] = builder
        self.__iterable: IEnumerable[T] = iterable

    @final
    def IsResumable(self) -> bool|None: return None
    
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
        def __init__(self, setter: Method[IEnumerable[_T]], finalizer: Action) -> None:
            super().__init__()

            self.__setter: Method[IEnumerable[_T]] = setter
            self.__finalizer: Action = finalizer
        
        def SetIterable(self, iterable: IEnumerable[_T]) -> None: return self.__setter(iterable)
        def UnsetIterable(self) -> None: return self.__finalizer()
    
    def __init__(self, iterable: IEnumerable[T]|Iterable[T]) -> None:
        super().__init__()

        self.__iterable: IEnumerable[T] = _Enumerable[T](IterableBuilder[T]._Cookie(self.__SetIterable, self.__UnsetIterable), AsEnumerable(iterable))
    
    @final
    def __UpdateIterable(self, iterable: IEnumerable[T]) -> None:
        self.__iterable = iterable
    
    @final
    def __SetIterable(self, iterable: IEnumerable[T]) -> None:
        self.__UpdateIterable(iterable)
    @final
    def __UnsetIterable(self) -> None:
        self.__UpdateIterable(GetEmptyEnumerable())

    @final
    def IsResumable(self) -> bool|None: return True
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__iterable.TryGetEnumerator()