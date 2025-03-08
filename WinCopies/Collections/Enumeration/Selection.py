from abc import abstractmethod
from typing import final

from WinCopies.Collections.Enumeration import IEnumerator, AbstractEnumeratorBase, SafeEnumerator
from WinCopies.Delegates import FuncAndAlso
from WinCopies.Typing.Delegate import Function, Predicate

class ConditionalEnumerator[T](AbstractEnumeratorBase[T, T, IEnumerator[T]], SafeEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)

    @abstractmethod
    def _Validate(self) -> bool:
        pass

    @final
    def _MoveNext(self) -> bool:
        if super()._MoveNextOverride():
            self._SetCurrent(self._GetEnumerator().GetCurrent())

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        while self._MoveNext():
            if self._Validate(self.__current):
                return True
        
        return False

class __PredicateEnumerator[T](IEnumerator[T]):
    def __init__(self, predicate: Predicate[T]):
        super().__init__()

        self.__predicate: Predicate[T] = predicate
    
    def _Validate(self) -> bool:
        return self.__predicate(self.GetCurrent())

class SelectorEnumerator[T](ConditionalEnumerator[T], __PredicateEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator, predicate)

class InclusionEnumerator[T](ConditionalEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _MoveNextOverride(self) -> bool:
        return self._MoveNext() and self._Validate(self.GetCurrent())
class IncluerEnumerator[T](InclusionEnumerator[T], __PredicateEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator, predicate)

class InclusionUntilEnumerator[T](ConditionalEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _Validate(self) -> bool:
        return not super()._Validate()
class IncluerEnumerator[T](InclusionUntilEnumerator[T], __PredicateEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator, predicate)

class DoWhileEnumerator[T](ConditionalEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)

        self.__moveNext: Function[bool]|None
    
    def _OnStarting(self) -> bool:
        def moveNext() -> bool:
            if self._MoveNext():
                self.__moveNext = FuncAndAlso(self._Validate, self._MoveNext)

                return True
            
            return False

        if super()._OnStarting():
            self.__moveNext = moveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__moveNext = None
class PredicateDoWhileEnumerator[T](DoWhileEnumerator[T], __PredicateEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator, predicate)

class DoUntilEnumerator[T](DoWhileEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _Validate(self) -> bool:
        return not super()._Validate()
class PredicateDoUntilEnumerator[T](DoUntilEnumerator[T], __PredicateEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)

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
        return self.__moveNext()
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__moveNext = None

class ExclusionUntilEnumerator[T](ExclusionEnumeratorBase[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _OnMoveNext(self) -> Function[bool]|None:
        while self._MoveNext():
            if self._Validate(self.GetCurrent()):
                return self._MoveNext
        
        return None
class ExcluerUntilEnumerator[T](ExclusionUntilEnumerator[T], __PredicateEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator, predicate)

class ExclusionEnumerator[T](ExclusionUntilEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        super().__init__(enumerator)
    
    def _Validate(self) -> bool:
        return not super()._Validate()
class ExcluerEnumerator[T](ExclusionEnumerator[T], __PredicateEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T], predicate: Predicate[T]):
        super().__init__(enumerator, predicate)