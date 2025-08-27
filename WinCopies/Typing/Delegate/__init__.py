from abc import abstractmethod
from typing import final, Callable

type Action = Callable[[], None]
type Method[T] = Callable[[T], None]
type Function[T] = Callable[[], T]
type Converter[TIn, TOut] = Callable[[TIn], TOut]
type Predicate[T] = Converter[T, bool]
type EqualityComparison[T] = Callable[[T, T], bool]
type IndexedValueComparison[T] = Callable[[int, T], bool]
type Selector[T] = Converter[T, T]

class IFunction[T]:
    def __init__(self):
        super().__init__()

    @abstractmethod
    def GetValue(self) -> T:
        pass

    @final
    def __call__(self) -> T:
        return self.GetValue()

@final
class ValueFunction[T](IFunction[T]):
    def __init__(self, value: T):
        super().__init__()

        self.__value: T = value
    
    def GetValue(self) -> T:
        return self.__value

class FunctionUpdater[T](IFunction[T]):
    def __init__(self, updater: Method[IFunction[T]]):
        super().__init__()

        self.__updater: Method[IFunction[T]] = updater
    
    @abstractmethod
    def _GetFunction(self) -> IFunction[T]:
        pass
    
    @final
    def GetValue(self) -> T:
        function: IFunction[T] = self._GetFunction()

        self.__updater(function)
        
        return function.GetValue()
class ValueFunctionUpdater[T](FunctionUpdater[T]):
    def __init__(self, updater: Method[IFunction[T]]):
        super().__init__(updater)
    
    @abstractmethod
    def _GetValue(self) -> T:
        pass
    
    @final
    def _GetFunction(self) -> IFunction[T]:
        return ValueFunction[T](self._GetValue())