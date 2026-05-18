from abc import abstractmethod
from collections.abc import Iterable, Collection, Sequence
from typing import final

from WinCopies.Collections import Generator, IReadOnlyCountableIndexable, MakeGenerator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ICountableEnumerable, NullableEnumerator, CreateIterable
from WinCopies.Delegates import BoolFalse, GetActionBoolFunc
from WinCopies.Typing.Delegate import Function, Predicate

def _GetCustomRange(start: int, stop: int) -> Iterable[int]:
    return range(start, stop)
def _GetRange(start: int, size: int) -> Iterable[int]:
    return _GetCustomRange(start, start + size)
def _GetDefaultRange(size: int) -> Iterable[int]:
    return _GetRange(0, size)

class RangeEnumerator(NullableEnumerator[Iterable[int]]):
    def __init__(self, size: int, count: int) -> None:
        super().__init__()

        self.__size: int = size
        self.__count: int = count

        self.__moveNext: Function[bool] = self.__MoveNext
    
    @final
    def __Enumerate(self, start: int) -> Iterable[int]:
        return _GetRange(start, self.GetSize())
    
    @final
    def __Decrement(self, length: int) -> int:
        return length - self.GetSize()
    
    @final
    def __Batch(self, length: int) -> bool:
        size: int = self.GetSize()
        start: int = size

        def update() -> None:
            nonlocal start
            nonlocal length

            start += size
            length = self.__Decrement(length)
        
        def check() -> bool:
            return size < length
        
        def setCurrent() -> None:
            self._SetCurrent(self.__Enumerate(start))
        def trySetCurrent() -> bool:
            if length > 0:
                self.__moveNext = BoolFalse

                self._SetCurrent(_GetCustomRange(start, self.GetCount()))

                return True
            
            return False
        
        def batch() -> bool:
            if check():
                setCurrent()

                return True
            
            return trySetCurrent()
        
        if check():
            setCurrent()

            self.__moveNext = GetActionBoolFunc(update, batch)
            
            return True
    
        return trySetCurrent()
    
    @final
    def __MoveNext(self) -> bool:
        count: int = self.GetCount()

        if count > 0:
            size: int = self.GetSize()
            
            if size >= count:
                self.__moveNext = BoolFalse

                self._SetCurrent(_GetDefaultRange(count))

                return True
            
            self.__moveNext = lambda: self.__Batch(self.__Decrement(self.GetCount()))

            self._SetCurrent(self.__Enumerate(0))

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _ResetOverride(self) -> bool:
        self.__moveNext = self.__MoveNext
        
        return True
    
    def _OnEnded(self) -> None:
        self.__moveNext = BoolFalse

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass
    
    def IsResetSupported(self) -> bool:
        return True
    
    @final
    def GetCount(self) -> int:
        return self.__count
    @final
    def GetSize(self) -> int:
        return self.__size

class IBatchEnumerator[T](IEnumerator[Generator[T]]):
    def __init__(self) -> None:
        super().__init__()
class BatchEnumerator[T](NullableEnumerator[Generator[T]], IBatchEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

class CountableBatchEnumerator[T](BatchEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetCount(self) -> int:
        pass

class IndexableBatchEnumeratorBase[T](CountableBatchEnumerator[T]):
    def __init__(self, size: int) -> None:
        super().__init__()

        self.__rangeEnumerator: RangeEnumerator = RangeEnumerator(size, self._GetCount())
    
    @final
    def GetSize(self) -> int:
        return self.__rangeEnumerator.GetSize()

    @abstractmethod
    def _GetAt(self, index: int) -> T:
        pass

    def _MoveNextOverride(self) -> bool:
        def enumerate(range: Iterable[int]) -> Generator[T]:
            for i in range:
                yield self._GetAt(i)
        
        enumerator: RangeEnumerator = self.__rangeEnumerator

        if enumerator.MoveNext():
            range: Iterable[int] = enumerator.GetCurrent()

            self._SetCurrent(enumerate(range))

            return True

        return False
    
    def _ResetOverride(self) -> bool:
        return self.__rangeEnumerator.TryReset() is True
    
    def _OnStopped(self) -> None:
        pass
    
    def _OnEnded(self) -> None:
        self.__rangeEnumerator.Stop()
    
    def IsResetSupported(self) -> bool:
        return True

class IndexableBatchEnumerator[T](IndexableBatchEnumeratorBase[T]):
    def __init__(self, size: int, items: IReadOnlyCountableIndexable[T]) -> None:
        super().__init__(size)

        self.__items: IReadOnlyCountableIndexable[T] = items
    
    @final
    def _GetCount(self) -> int:
        return self.__items.GetCount()
    
    @final
    def _GetAt(self, index: int) -> T:
        return self.__items.GetAt(index)
class SequenceBatchEnumerator[T](IndexableBatchEnumeratorBase[T]):
    def __init__(self, size: int, items: Sequence[T]) -> None:
        super().__init__(size)

        self.__items: Sequence[T] = items
    
    @final
    def _GetCount(self) -> int:
        return len(self.__items)
    
    @final
    def _GetAt(self, index: int) -> T:
        return self.__items[index]

class BufferedBatchEnumeratorBase[T](BatchEnumerator[T]):
    def __init__(self, size: int, enumerator: IEnumerator[T], safe: bool = True) -> None:
        super().__init__()

        self.__size: int = size
        self.__enumerator: IEnumerator[T] = enumerator

        self.__moveNext: Function[bool] = self._MoveNext
        self.__batch: Predicate[IEnumerator[T]] = self.__SafeBatch if safe else self.__Batch
    
    def __Batch(self, enumerator: IEnumerator[T]) -> bool:
        def enumerate() -> Generator[T]:
            for _ in _GetDefaultRange(self._GetSize()):
                if enumerator.MoveNext():
                    yield enumerator.GetCurrent()
                
                else:
                    break
        
        def moveNext() -> bool:
            if enumerator.IsStarted():
                self._SetCurrent(enumerate())

                return True
            
            return False
        
        self._SetCurrent(enumerate())

        self.__moveNext = moveNext

        return True
    def __SafeBatch(self, enumerator: IEnumerator[T]) -> bool:
        def enumerate() -> Generator[T]:
            def enumerate() -> Generator[T]:
                for _ in _GetCustomRange(1, self._GetSize()):
                    if enumerator.MoveNext():
                        yield enumerator.GetCurrent()
                    
                    else:
                        break
            
            yield enumerator.GetCurrent()
            
            for item in enumerate():
                yield item
        def iterate() -> Generator[T]:
            yield enumerator.GetCurrent()
        
        def getGenerator(func: Function[Generator[T]]) -> bool:
            if enumerator.MoveNext():
                self._SetCurrent(func())

                return True
            
            return False
        
        if enumerator.MoveNext():
            func: Function[Generator[T]] = iterate if self._GetSize() == 1 else enumerate
            self.__moveNext = lambda: getGenerator(func)

            self._SetCurrent(func())

            return True
        
        return False

    @final
    def _GetSize(self) -> int:
        return self.__size
    
    @final
    def _GetEnumerator(self) -> IEnumerator[T]:
        return self.__enumerator

    def _MoveNext(self) -> bool:
        return self.__batch(self.__enumerator)
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _ResetOverride(self) -> bool:
        if self.__enumerator.TryReset() is True:
            self.__moveNext = self._MoveNext

            return True
        
        return False
    
    @final
    def _UnsetMoveNext(self) -> None:
        self.__moveNext = BoolFalse
    
    def _OnStopped(self) -> None:
        pass
    
    def _OnEnded(self) -> None:
        self._UnsetMoveNext()
    
    def IsResetSupported(self) -> bool:
        return self.__enumerator.IsResetSupported()
class BufferedBatchEnumerator[T](BufferedBatchEnumeratorBase[T]):
    def __init__(self, size: int, enumerator: IEnumerator[T], safe: bool = True) -> None:
        super().__init__(size, enumerator, safe)

class BufferedCountableBatchEnumeratorBase[T](BufferedBatchEnumeratorBase[T]):
    def __init__(self, size: int, enumerator: IEnumerator[T]) -> None:
        super().__init__(size, enumerator)
    
    @abstractmethod
    def _GetCount(self) -> int:
        pass

    def _MoveNext(self) -> bool:
        def iterate() -> Generator[T]:
            for item in self._GetEnumerator().AsIterator():
                yield item
        
        count: int = self._GetCount()
        
        if count < 1:
            return False
        
        if self._GetSize() >= count:
            self._UnsetMoveNext()

            self._SetCurrent(iterate())

            return True
        
        return super()._MoveNext()

class BufferedCountableBatchEnumerator[T](BufferedCountableBatchEnumeratorBase[T]):
    def __init__(self, size: int, items: ICountableEnumerable[T]) -> None:
        super().__init__(size, items.GetEnumerator())

        self.__items: ICountableEnumerable[T] = items
    
    @final
    def _GetCount(self) -> int:
        return self.__items.GetCount()
class BufferedCollectionBatchEnumerator[T](BufferedCountableBatchEnumeratorBase[T]):
    def __init__(self, size: int, items: Collection[T]) -> None:
        super().__init__(size, CreateIterable(items).GetEnumerator())

        self.__items: Collection[T] = items
    
    @final
    def _GetCount(self) -> int:
        return len(self.__items)

def Batch[T](items: IReadOnlyCountableIndexable[T]|ICountableEnumerable[T]|IEnumerable[T]|Sequence[T]|Collection[T]|Iterable[T], size: int, safe: bool = True) -> Generator[Generator[T]]:
    def tryCreateEnumerator(items: IEnumerable[T]) -> IBatchEnumerator[T]|None:
        enumerator: IEnumerator[T]|None = items.TryGetEnumerator()

        return None if enumerator is None else BufferedBatchEnumerator[T](size, enumerator, safe)

    def batch() -> IBatchEnumerator[T]|None:
        match items:
            case IReadOnlyCountableIndexable():
                return IndexableBatchEnumerator[T](size, items)
            case Sequence():
                return SequenceBatchEnumerator[T](size, items)
            
            case ICountableEnumerable():
                return BufferedCountableBatchEnumerator[T](size, items)
            case Collection():
                return BufferedCollectionBatchEnumerator[T](size, items)
            
            case IEnumerable():
                return tryCreateEnumerator(items)
            case _:
                return tryCreateEnumerator(CreateIterable(items))
    
    def enumerate(enumerator: IBatchEnumerator[T]) -> Generator[Generator[T]]:
        for _batch in enumerator.AsIterator():
            yield _batch
    
    enumerator: IBatchEnumerator[T]|None = batch()

    return MakeGenerator() if enumerator is None else enumerate(enumerator)