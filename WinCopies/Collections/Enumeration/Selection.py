from abc import abstractmethod
from typing import final

from WinCopies import IInterface
from WinCopies.Collections.Enumeration import IEnumerator, AbstractEnumerator
from WinCopies.Delegates import GetAndAlsoFunc
from WinCopies.Typing.Delegate import Function, Predicate

class ConditionalEnumerator[T](AbstractEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)

        self.__current: T|None = None
    
    def GetCurrent(self) -> T|None:
        return self.__current

    @abstractmethod
    def _Validate(self) -> bool:
        pass

    @final
    def _MoveNext(self) -> bool:
        if super()._MoveNextOverride():
            self.__current = self.GetCurrent()

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        while self._MoveNext():
            if self._Validate():
                return True
        
        return False
    
    def _OnStopped(self) -> None:
        pass

class _PredicateEnumerator[T](IInterface):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__()
        
        self.__enumerator: IEnumerator[T] = enumerator
        self.__predicate: Predicate[T] = predicate
    
    def Validate(self) -> bool:
        current: T|None = self.__enumerator.GetCurrent()

        return False if current is None else self.__predicate(current)

class SelectorEnumerator[T](ConditionalEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator)

        self.__predicate: _PredicateEnumerator[T] = _PredicateEnumerator[T](enumerator, predicate)
    
    def _Validate(self) -> bool:
        return self.__predicate.Validate()

class InclusionEnumerator[T](ConditionalEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _MoveNextOverride(self) -> bool:
        return self._MoveNext() and self._Validate()
class IncluerUntilEnumerator[T](InclusionEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator)

        self.__predicate: _PredicateEnumerator[T] = _PredicateEnumerator[T](enumerator, predicate)
    
    def _Validate(self) -> bool:
        return self.__predicate.Validate()

class InclusionUntilEnumerator[T](ConditionalEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _Validate(self) -> bool:
        return not super()._Validate()
class IncluerEnumerator[T](InclusionUntilEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator)

        self.__predicate: _PredicateEnumerator[T] = _PredicateEnumerator[T](enumerator, predicate)
    
    def _Validate(self) -> bool:
        return self.__predicate.Validate()

class DoWhileEnumerator[T](ConditionalEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)

        self.__moveNext: Function[bool]|None
    
    def _OnStarting(self) -> bool:
        def moveNext() -> bool:
            if self._MoveNext():
                self.__moveNext = GetAndAlsoFunc(self._Validate, self._MoveNext)

                return True
            
            return False

        if super()._OnStarting():
            self.__moveNext = moveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext is not None and self.__moveNext()
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__moveNext = None
class PredicateDoWhileEnumerator[T](DoWhileEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator)

        self.__predicate: _PredicateEnumerator[T] = _PredicateEnumerator[T](enumerator, predicate)
    
    def _Validate(self) -> bool:
        return self.__predicate.Validate()

class DoUntilEnumerator[T](DoWhileEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator)

        self.__predicate: _PredicateEnumerator[T] = _PredicateEnumerator[T](enumerator, predicate)
    
    def _Validate(self) -> bool:
        return not self.__predicate.Validate()
class PredicateDoUntilEnumerator[T](DoUntilEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator, predicate)

class ExclusionEnumeratorBase[T](ConditionalEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)

        self.__moveNext: Function[bool]|None
    
    @abstractmethod
    def _OnMoveNext(self) -> Function[bool]|None:
        pass
    
    def _OnStarting(self) -> bool:
        def moveNext() -> bool:
            func: Function[bool]|None = self._OnMoveNext()

            if func is None:
                return False
            
            self.__moveNext = func

            return True

        if super()._OnStarting():
            self.__moveNext = moveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext is not None and self.__moveNext()
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__moveNext = None

class ExclusionUntilEnumerator[T](ExclusionEnumeratorBase[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _OnMoveNext(self) -> Function[bool]|None:
        while self._MoveNext():
            if self._Validate():
                return self._MoveNext
        
        return None
class ExcluerUntilEnumerator[T](ExclusionUntilEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator)

        self.__predicate: _PredicateEnumerator[T] = _PredicateEnumerator[T](enumerator, predicate)
    
    def _Validate(self) -> bool:
        return self.__predicate.Validate()

class ExclusionEnumerator[T](ExclusionUntilEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _Validate(self) -> bool:
        return not super()._Validate()
class ExcluerEnumerator[T](ExclusionEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator)

        self.__predicate: _PredicateEnumerator[T] = _PredicateEnumerator[T](enumerator, predicate)
    
    def _Validate(self) -> bool:
        return self.__predicate.Validate()