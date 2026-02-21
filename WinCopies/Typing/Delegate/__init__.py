from abc import abstractmethod
from typing import final, Callable

from WinCopies import IInterface, Abstract
from WinCopies.Typing.Generic import GenericConstraint

type Action = Callable[[], None]
type Method[T] = Callable[[T], None]
type Function[T] = Callable[[], T]
type NullableFunction[T] = Callable[[], T|None]
type Converter[TIn, TOut] = Callable[[TIn], TOut]
type NullableConverter[TIn, TOut] = Converter[TIn, TOut|None]
type Predicate[T] = Converter[T, bool]
type NullablePredicate[T] = Converter[T, bool|None]
type EqualityComparison[T] = Callable[[T, T], bool]
type IndexedValueFunction[TIn, TOut] = Callable[[int, TIn], TOut]
type IndexedValueAction[T] = IndexedValueFunction[T, None]
type IndexedValueComparison[T] = IndexedValueFunction[T, bool]
type Selector[T] = Converter[T, T]

class IFunctionBase[T](IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def GetValue(self) -> T:
        pass
class IFunction[T](IFunctionBase[T]):
    def __init__(self) -> None:
        super().__init__()

    @final
    def __call__(self) -> T:
        return self.GetValue()
class IMethodBase[T](IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass
class IMethod[T](IMethodBase[T]):
    def __init__(self) -> None:
        super().__init__()

    @final
    def __call__(self, value: T) -> None:
        self.SetValue(value)

@final
class ValueFunction[T](Abstract, IFunction[T]):
    def __init__(self, value: T) -> None:
        super().__init__()

        self.__value: T = value
    
    def GetValue(self) -> T:
        return self.__value

class FunctionUpdater[T](Abstract, IFunction[T]):
    def __init__(self, updater: Method[IFunction[T]]) -> None:
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
    def __init__(self, updater: Method[IFunction[T]]) -> None:
        super().__init__(updater)
    
    @abstractmethod
    def _GetValue(self) -> T:
        pass
    
    @final
    def _GetFunction(self) -> IFunction[T]:
        return ValueFunction[T](self._GetValue())

class SelectionUpdater[TClass, TInterface](ValueFunctionUpdater[TInterface], GenericConstraint[TClass, TInterface]):
    def __init__(self, value: TClass, updater: Method[IFunction[TInterface]]) -> None:
        super().__init__(updater)

        self.__value: TClass = value
    
    @final
    def _GetContainer(self) -> TClass:
        return self.__value
    
    def _GetValue(self) -> TInterface:
        return self._AsContainer(self._GetContainer())

@final
class __DefaultFunction(Abstract, IFunction[None]):
    def __init__(self) -> None:
        super().__init__()
    
    def GetValue(self) -> None:
        return None

__getDefaultFunction: IFunction[None] = __DefaultFunction()

def GetDefaultFunction() -> IFunction[None]:
    return __getDefaultFunction

@final
class _ValueProviderUpdater[T](ValueFunctionUpdater[T]):
    def __init__(self, valueProvider: IFunction[T], updater: Method[IFunction[T]]) -> None:
        super().__init__(updater)

        self.__valueProvider: IFunction[T] = valueProvider
    
    def _GetValue(self) -> T:
        return self.__valueProvider.GetValue()

@final
class ValueProvider[T](Abstract, IFunction[T]):
    def __init__(self, valueProvider: IFunction[T]) -> None:
        def update(func: IFunction[T]) -> None:
            self.__valueProvider = func
        
        super().__init__()

        self.__valueProvider: IFunction[T] = _ValueProviderUpdater[T](valueProvider, update) # type: ignore[no-redef]
    
    def GetValue(self) -> T:
        return self.__valueProvider.GetValue()

class IStruct[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> T:
        pass
    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass
@final
class Struct[T](Abstract, IStruct[T]):
    def __init__(self, value: T) -> None:
        super().__init__()

        self.__value: T = value
    
    def GetValue(self) -> T:
        return self.__value
    def SetValue(self, value: T) -> None:
        self.__value = value