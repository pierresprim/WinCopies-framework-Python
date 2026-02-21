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

class IStructBase[T](IFunctionBase[T], IMethodBase[T]):
    def __init__(self) -> None:
        super().__init__()
class IStruct[T](IStructBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsFunction(self) -> IFunction[T]:
        pass
    @abstractmethod
    def AsMethod(self) -> IMethod[T]:
        pass

@final
class _StructFunction[T](IFunction[T]):
    def __init__(self, struct: IStruct[T]) -> None:
        super().__init__()

        self.__struct: IStruct[T] = struct
    
    def GetValue(self) -> T:
        return self.__struct.GetValue()
@final
class _StructMethod[T](IMethod[T]):
    def __init__(self, struct: IStruct[T]) -> None:
        super().__init__()

        self.__struct: IStruct[T] = struct
    
    def SetValue(self, value: T) -> None:
        return self.__struct.SetValue(value)

@final
class _StructFunctionUpdater[T](ValueFunctionUpdater[IFunction[T]]):
    def __init__(self, struct: IStruct[T], updater: Method[IFunction[IFunction[T]]]) -> None:
        super().__init__(updater)

        self.__struct: IStruct[T] = struct
    
    def _GetValue(self) -> IFunction[T]:
        return _StructFunction[T](self.__struct)
@final
class _StructMethodUpdater[T](ValueFunctionUpdater[IMethod[T]]):
    def __init__(self, struct: IStruct[T], updater: Method[IFunction[IMethod[T]]]) -> None:
        super().__init__(updater)

        self.__struct: IStruct[T] = struct
    
    def _GetValue(self) -> IMethod[T]:
        return _StructMethod[T](self.__struct)

class StructBase[T](Abstract, IStruct[T]):
    def __init__(self) -> None:
        def updateFunction(func: IFunction[IFunction[T]]) -> None:
            self.__function = func
        def updateMethod(func: IFunction[IMethod[T]]) -> None:
            self.__method = func
        
        super().__init__()

        self.__function: IFunction[IFunction[T]] = _StructFunctionUpdater[T](self, updateFunction) # type: ignore[no-redef]
        self.__method: IFunction[IMethod[T]] = _StructMethodUpdater[T](self, updateMethod) # type: ignore[no-redef]
    
    def AsFunction(self) -> IFunction[T]:
        return self.__function.GetValue()
    def AsMethod(self) -> IMethod[T]:
        return self.__method.GetValue()
@final
class Struct[T](StructBase[T]):
    def __init__(self, value: T) -> None:
        super().__init__()

        self.__value: T = value
    
    def GetValue(self) -> T:
        return self.__value
    def SetValue(self, value: T) -> None:
        self.__value = value

class StructUpdater[T](Abstract, IStructBase[T]):
    def __init__(self, updater: Method[IStruct[T]]) -> None:
        super().__init__()

        self.__updater: Method[IStruct[T]] = updater
    
    @abstractmethod
    def _GetStruct(self, value: T) -> IStruct[T]:
        pass
    @abstractmethod
    def _GetValue(self) -> T:
        pass
    
    @final
    def GetValue(self) -> T:
        struct: IStruct[T] = self._GetStruct(self._GetValue())

        self.__updater(struct)
        
        return struct.GetValue()
    @final
    def SetValue(self, value: T) -> None:
        struct: IStruct[T] = self._GetStruct(value)

        self.__updater(struct)
        
        return struct.SetValue(value)
class ValueStructUpdater[T](StructUpdater[T]):
    def __init__(self, updater: Method[IStruct[T]]) -> None:
        super().__init__(updater)
    
    @final
    def _GetStruct(self, value: T) -> IStruct[T]:
        return Struct[T](value)

@final
class _HandleUpdater[T](ValueStructUpdater[T]):
    def __init__(self, valueProvider: IFunctionBase[T], updater: Method[IStruct[T]]) -> None:
        super().__init__(updater)

        self.__valueProvider: IFunctionBase[T] = valueProvider
    
    def _GetValue(self) -> T:
        return self.__valueProvider.GetValue()

@final
class Handle[T](StructBase[T]):
    def __init__(self, valueProvider: IFunctionBase[T]) -> None:
        def update(struct: IStructBase[T]) -> None:
            self.__struct = struct
        
        super().__init__()

        self.__struct: IStructBase[T] = _HandleUpdater[T](valueProvider, update) # type: ignore[no-redef]
    
    def GetValue(self) -> T:
        return self.__struct.GetValue()
    def SetValue(self, value: T) -> None:
        self.__struct.SetValue(value)