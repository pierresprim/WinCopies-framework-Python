from abc import abstractmethod
from collections.abc import Iterable, Collection, Sequence
from typing import Callable, final

from WinCopies.Collections import Generator
from WinCopies.Collections.Core import IReadOnlyCountableIndexable
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ICountableEnumerable, NullableEnumerator, AbstractEnumeratorBase, CreateIterable
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerable, IResumableCountableEnumerable, IResumableEnumerator as IResumableEnumeratorBase, IResumableEnumerationCursor
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Doubly import IList, List, IDoublyLinkedNode
from WinCopies.Collections.Util import Enumerate, MakeGenerator
from WinCopies.Delegates import NoAction, BoolFalse, AlwaysFalse, GetActionBoolFunc
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Action, Function, NullablePredicate
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

def _GetCustomRange(start: int, stop: int) -> Iterable[int]:
    return range(start, stop)
def _GetRange(start: int, size: int) -> Iterable[int]:
    return _GetCustomRange(start, start + size)
def _GetDefaultRange(size: int) -> Iterable[int]:
    return _GetRange(0, size)

def _Enumerate[T](enumerator: IEnumerator[T], size: int) -> Generator[T]:
    def iterate() -> Generator[T]:
        yield enumerator.GetCurrent()
    
    def enumerate() -> Generator[T]:
        def enumerate() -> Generator[T]:
            for _ in _GetCustomRange(1, size):
                if enumerator.MoveNext():
                    yield enumerator.GetCurrent()
                
                else:
                    break
        
        yield enumerator.GetCurrent()
        
        for item in enumerate():
            yield item
    
    return iterate() if size == 1 else enumerate()

def _CompleteBatch[T](batch: Generator[T]) -> None:
    for _ in batch:
        pass

class IResumableEnumerator[T](IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def CanResume(self) -> bool:
        pass
    
    @abstractmethod
    def TryResume(self, size: int) -> bool|None:
        pass
class ResumableEnumerator[T](NullableEnumerator[T], IResumableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _TryResumeOverride(self, size: int) -> bool|None:
        pass
    
    def CanResume(self) -> bool:
        return self.IsStarted()
    
    @final
    def TryResume(self, size: int) -> bool|None:
        if self.CanResume():
            result: bool|None = self._TryResumeOverride(size)

            if result is False:
                return False

            self._UnsetCurrent()

            return result
        
        return False

class IRangeEnumerator(IResumableEnumerator[Iterable[int]]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetCount(self) -> int:
        pass
    
    @abstractmethod
    def GetSize(self) -> int:
        pass
class RangeEnumerator(ResumableEnumerator[Iterable[int]], IRangeEnumerator):
    def __init__(self, size: int, count: int) -> None:
        super().__init__()

        self.__size: int = size
        self.__count: int = count

        self.__moveNext: Function[bool] = self.__MoveNext
        self.__resume: Action = NoAction
    
    @final
    def __Enumerate(self, start: int) -> Iterable[int]:
        return _GetRange(start, self.GetSize())
    
    @final
    def __Decrement(self, length: int) -> int:
        return length - self.GetSize()
    
    @final
    def __Batch(self, start: int, length: int) -> bool:
        def updateResume() -> None:
            def resume() -> None:
                self.__moveNext = lambda: self.__Batch(start, length)
            
            self.__resume = resume
        
        size: int = self.GetSize()

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
                updateResume()

                return True
            
            if trySetCurrent():
                updateResume()

                return True
            
            return False
        
        if check():
            setCurrent()
            updateResume()

            self.__moveNext = GetActionBoolFunc(update, batch)
            
            return True
    
        if trySetCurrent():
            updateResume()

            return True
        
        return False
    
    @final
    def __MoveNext(self) -> bool:
        def resume() -> None:
            self.__moveNext = self.__MoveNext
        
        count: int = self.GetCount()

        if count < 1:
            return False
        
        size: int = self.GetSize()
        
        if size >= count:
            self.__moveNext = BoolFalse
            
            self._SetCurrent(_GetDefaultRange(count))

        else:
            self.__moveNext = lambda: self.__Batch(size, self.__Decrement(self.GetCount()))
            
            self._SetCurrent(self.__Enumerate(0))

        self.__resume = resume

        return True
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    @final
    def _TryResumeOverride(self, size: int) -> bool|None:
        self.__resume()
        self.__size = size

        return True
    
    def _ResetOverride(self) -> bool:
        self.__moveNext = self.__MoveNext
        
        return True
    
    def _OnEnded(self) -> None:
        self.__moveNext = BoolFalse
        self.__resume = NoAction

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

class IResumableBatchEnumerator[T](IBatchEnumerator[T], IResumableEnumerator[Generator[T]]):
    def __init__(self) -> None:
        super().__init__()
class ResumableBatchEnumeratorAbstract[T](ResumableEnumerator[Generator[T]], IResumableBatchEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

    def _OnCurrentInvalidated(self, old: Generator[T]) -> None:
        old.close()

        super()._OnCurrentInvalidated(old)

class CountableBatchEnumerator[T](ResumableBatchEnumeratorAbstract[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetCount(self) -> int:
        pass

class IndexableBatchEnumeratorBase[T](CountableBatchEnumerator[T]):
    def __init__(self, size: int) -> None:
        super().__init__()

        self.__rangeEnumerator: RangeEnumerator = RangeEnumerator(size, self._GetCount())

    @abstractmethod
    def _GetAt(self, index: int) -> T:
        pass

    def _MoveNextOverride(self) -> bool:
        def enumerate(range: Iterable[int]) -> Generator[T]:
            return Select(range, self._GetAt)
        
        enumerator: RangeEnumerator = self.__rangeEnumerator

        if enumerator.MoveNext():
            range: Iterable[int] = enumerator.GetCurrent()

            self._SetCurrent(enumerate(range))

            return True

        return False
    
    def _TryResumeOverride(self, size: int) -> bool|None:
        return self.__rangeEnumerator.TryResume(size)
    
    def _ResetOverride(self) -> bool:
        return self.__rangeEnumerator.TryReset() is True
    
    def _OnStopped(self) -> None:
        pass
    
    def _OnEnded(self) -> None:
        self.__rangeEnumerator.Stop()

        super()._OnEnded()
    
    def IsResetSupported(self) -> bool:
        return True
    
    @final
    def GetSize(self) -> int:
        return self.__rangeEnumerator.GetSize()

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

class IResumableBatchInnerEnumerator[T](IEnumerator[Generator[T]]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryResume(self, size: int) -> bool|None:
        pass
class _ResumableBatchInnerEnumeratorBase[T](AbstractEnumeratorBase[T, Generator[T], IResumableEnumeratorBase[T]], IResumableBatchInnerEnumerator[T], IGenericConstraintImplementation[IResumableEnumeratorBase[T]]):
    def __init__(self, enumerator: IResumableEnumeratorBase[T], size: int) -> None:
        super().__init__(enumerator)

        self.__current: Generator[T]|None = None
        self.__cursor: IResumableEnumerationCursor|None = None
        
        self.__size: int = size
        
        self.__moveNext: Function[bool] = self.__MoveFirst
    
    @final
    def _GetSize(self) -> int:
        return self.__size
    
    @final
    def _SetCurrent(self, generator: Generator[T]) -> None:
        self.__current = generator
    
    @final
    def _PlaceCursor(self, enumerator: IResumableEnumeratorBase[T]) -> None:
        self.__cursor = enumerator.PlaceCursor()
    
    @abstractmethod
    def _MoveFirst(self, enumerator: IResumableEnumeratorBase[T]) -> bool:
        pass
    
    @final
    def _SetCurrentDefault(self, enumerator: IResumableEnumeratorBase[T]) -> None:
        def enumerate() -> Generator[T]:
            getCurrent: Function[T]

            def __getCurrent() -> T:
                return enumerator.GetCurrent()
            def _getCurrent() -> T:
                nonlocal getCurrent
                
                self._PlaceCursor(enumerator)

                return (getCurrent := __getCurrent)()

            getCurrent = _getCurrent
            
            for _ in _GetDefaultRange(self._GetSize()):
                if enumerator.MoveNext():
                    yield getCurrent()
                
                else:
                    break
        
        self._SetCurrent(enumerate())
        
    @final
    def __MoveNext(self, enumerator: IResumableEnumeratorBase[T]) -> None:
        old: Generator[T]|None = self.__current

        if old is not None:
            _CompleteBatch(old)

            cursor: IResumableEnumerationCursor|None = self.__cursor

            if cursor is not None:
                cursor.Dispose()

                self.__cursor = None
        
        self._SetCurrentDefault(enumerator)
    @final
    def __MoveFirst(self) -> bool:
        def moveNext() -> bool:
            if enumerator.IsStarted():
                self.__MoveNext(enumerator)

                return True
            
            return False

        enumerator: IResumableEnumeratorBase[T] = self._GetContainer()

        self.__moveNext = moveNext

        return self._MoveFirst(enumerator)
    
    def _GetCurrent(self) -> Generator[T]:
        current: Generator[T]|None = self.__current

        if current is None:
            raise InvalidOperationError()
        
        return current
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _OnEnded(self) -> None:
        self.__moveNext = BoolFalse
    
        cursor: IResumableEnumerationCursor|None = self.__cursor

        if cursor is not None:
            cursor.Dispose()

            self.__cursor = None
        
        self.__current = None

        super()._OnEnded()
    
    def TryResume(self, size: int) -> bool|None:
        cursor: IResumableEnumerationCursor|None = self.__cursor

        if cursor is None:
            return False
        
        cursor.Resume()
        
        if self.__size == size:
            return None
        
        self.__size = size

        return True

@final
class _ResumableBatchInnerEnumerator[T](_ResumableBatchInnerEnumeratorBase[T]):
    def __init__(self, enumerator: IResumableEnumeratorBase[T], size: int) -> None:
        super().__init__(enumerator, size)
    
    def _MoveFirst(self, enumerator: IResumableEnumeratorBase[T]) -> bool:
        self._SetCurrentDefault(enumerator)
        
        return True
@final
class _ResumableBatchSafeInnerEnumerator[T](_ResumableBatchInnerEnumeratorBase[T]):
    def __init__(self, enumerator: IResumableEnumeratorBase[T], size: int) -> None:
        super().__init__(enumerator, size)
    
    def _MoveFirst(self, enumerator: IResumableEnumeratorBase[T]) -> bool:
        if enumerator.MoveNext():
            self._SetCurrent(_Enumerate(enumerator, self._GetSize()))
            
            self._PlaceCursor(enumerator)

            return True
        
        return False

class ResumableBatchEnumeratorBase[TItem, TEnumerable](ResumableBatchEnumeratorAbstract[TItem], GenericConstraint[TEnumerable, IResumableEnumerable[TItem]]):
    def __init__(self, size: int, items: TEnumerable) -> None:
        super().__init__()

        self.__items: TEnumerable = items
        self.__size: int = size

        self.__moveNext: Function[bool] = self._MoveNext
        self.__tryResume: NullablePredicate[int] = AlwaysFalse
    
    def _CreateEnumerator(self, enumerator: IResumableEnumeratorBase[TItem], size: int) -> IResumableBatchInnerEnumerator[TItem]:
        return _ResumableBatchInnerEnumerator[TItem](enumerator, size)
    
    @final
    def _Enumerate(self) -> bool:
        def tryGetEnumerator(size: int) -> IResumableBatchInnerEnumerator[TItem]|None:
            enumerator: IResumableEnumeratorBase[TItem]|None = items.TryGetResumableEnumerator()

            return None if enumerator is None else self._CreateEnumerator(enumerator, size)
        
        def moveNext(enumerator: IResumableBatchInnerEnumerator[TItem]) -> bool:
            if enumerator.MoveNext():
                self._SetCurrent(enumerator.GetCurrent())

                return True
            
            return False
        
        items: IResumableEnumerable[TItem] = self._GetInnerContainer()
        size: int = self._GetSize()

        enumerator: IResumableBatchInnerEnumerator[TItem]|None = tryGetEnumerator(size)

        if enumerator is None:
            return False

        self.__moveNext = lambda: moveNext(enumerator)
        self.__tryResume = lambda size: enumerator.TryResume(size)

        return self.__moveNext()
    
    @final
    def _GetContainer(self) -> TEnumerable:
        return self.__items
    
    @final
    def _GetSize(self) -> int:
        return self.__size
    
    @abstractmethod
    def _MoveNext(self) -> bool:
        pass
    
    @final
    def _DoMoveNext(self) -> bool:
        return self.__moveNext()
    
    def _MoveNextOverride(self) -> bool:
        return self._DoMoveNext()
    
    @final
    def _SetMoveNext(self, func: Function[bool]) -> None:
        self.__moveNext = func
    @final
    def _UnsetMoveNext(self) -> None:
        self.__moveNext = BoolFalse
    
    @final
    def _SetTryResume(self, predicate: NullablePredicate[int]) -> None:
        self.__tryResume = predicate
    
    def _TryResumeOverride(self, size: int) -> bool|None:
        result: bool|None = self.__tryResume(size)

        if result is True:
            self.__size = size

        return result
    
    def _ResetOverride(self) -> bool:
        self.__moveNext = self._MoveNext
        self.__tryResume = AlwaysFalse

        return True
    
    def _OnStopped(self) -> None:
        pass
    
    def _OnEnded(self) -> None:
        self.__moveNext = BoolFalse
        self.__tryResume = AlwaysFalse

        super()._OnEnded()
    
    def IsResetSupported(self) -> bool:
        return True

class ResumableBatchEnumerator[T](ResumableBatchEnumeratorBase[T, IResumableEnumerable[T]], IGenericConstraintImplementation[IResumableEnumerable[T]]):
    def __init__(self, size: int, items: IResumableEnumerable[T], safe: bool = True) -> None:
        super().__init__(size, items)

        self.__createEnumerator: Callable[[IResumableEnumeratorBase[T], int], IResumableBatchInnerEnumerator[T]] = self._CreateSafeEnumerator if safe else self._CreateUnsafeEnumerator
    
    def _CreateEnumerator(self, enumerator: IResumableEnumeratorBase[T], size: int) -> IResumableBatchInnerEnumerator[T]:
        return self.__createEnumerator(enumerator, size)
    
    @final
    def _CreateSafeEnumerator(self, enumerator: IResumableEnumeratorBase[T], size: int) -> IResumableBatchInnerEnumerator[T]:
        return _ResumableBatchSafeInnerEnumerator[T](enumerator, size)
    @final
    def _CreateUnsafeEnumerator(self, enumerator: IResumableEnumeratorBase[T], size: int) -> IResumableBatchInnerEnumerator[T]:
        return super()._CreateEnumerator(enumerator, size)
    
    def _MoveNext(self) -> bool:
        return self._Enumerate()
class ResumableCountableBatchEnumerator[T](ResumableBatchEnumeratorBase[T, IResumableCountableEnumerable[T]], IGenericConstraintImplementation[IResumableCountableEnumerable[T]]):
    def __init__(self, size: int, items: IResumableCountableEnumerable[T]) -> None:
        super().__init__(size, items)
    
    def _MoveNext(self) -> bool:
        def tryResume(_: int) -> bool:
            self._SetMoveNext(self._MoveNext)

            return True

        count: int = self._GetCount()

        if count < 1:
            return False
        
        items: IResumableCountableEnumerable[T] = self._GetContainer()
        size: int = self._GetSize()
        
        if size < count:
            return self._Enumerate()
        
        self._SetCurrent(Enumerate(items.AsIterable()))

        self._UnsetMoveNext()
        self._SetTryResume(tryResume)

        return True
    
    @final
    def _GetCount(self) -> int:
        return self._GetContainer().GetCount()

class BufferedBatchEnumeratorBase[T](BatchEnumerator[T]):
    def __init__(self, size: int, enumerator: IEnumerator[T]) -> None:
        super().__init__()

        self.__size: int = size
        self.__enumerator: IEnumerator[T] = enumerator

        self.__moveNext: Function[bool] = self._MoveNext
    
    def _OnCurrentUpdating(self, old: Generator[T]|None, new: Generator[T]) -> None:
        if old is not None:
            _CompleteBatch(old)

        super()._OnCurrentUpdating(old, new)
    
    def _Enumerate(self) -> bool:
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
        
        enumerator: IEnumerator[T] = self._GetEnumerator()
        
        self._SetCurrent(enumerate())
        self._SetMoveNext(moveNext)

        return True

    @final
    def _GetSize(self) -> int:
        return self.__size
    
    @final
    def _GetEnumerator(self) -> IEnumerator[T]:
        return self.__enumerator

    @abstractmethod
    def _MoveNext(self) -> bool:
        pass
    @final
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()
    
    def _ResetOverride(self) -> bool:
        if self.__enumerator.TryReset() is True:
            self.__moveNext = self._MoveNext

            return True
        
        return False
    
    @final
    def _SetMoveNext(self, func: Function[bool]) -> None:
        self.__moveNext = func
    @final
    def _UnsetMoveNext(self) -> None:
        self.__moveNext = BoolFalse
    
    def _OnStopped(self) -> None:
        pass
    
    def _OnEnded(self) -> None:
        self._UnsetMoveNext()
        
        super()._OnEnded()
    
    def IsResetSupported(self) -> bool:
        return self.__enumerator.IsResetSupported()
class BufferedBatchEnumerator[T](BufferedBatchEnumeratorBase[T]):
    def __init__(self, size: int, enumerator: IEnumerator[T], safe: bool = True) -> None:
        super().__init__(size, enumerator)

        self.__batch: Function[bool] = self.__EnumerateSafe if safe else self._Enumerate
    
    def __EnumerateSafe(self) -> bool:
        def getGenerator(func: Function[Generator[T]]) -> bool:
            if enumerator.MoveNext():
                self._SetCurrent(func())

                return True
            
            return False
        
        enumerator: IEnumerator[T] = self._GetEnumerator()
        
        if enumerator.MoveNext():
            func: Function[Generator[T]] = lambda: _Enumerate(enumerator, self._GetSize())

            self._SetMoveNext(lambda: getGenerator(func))
            self._SetCurrent(func())

            return True
        
        return False
    
    def _MoveNext(self) -> bool:
        return self.__batch()

class BufferedCountableBatchEnumeratorBase[T](BufferedBatchEnumeratorBase[T]):
    def __init__(self, size: int, enumerator: IEnumerator[T]) -> None:
        super().__init__(size, enumerator)
    
    @abstractmethod
    def _GetCount(self) -> int:
        pass

    def _MoveNext(self) -> bool:
        count: int = self._GetCount()
        
        if count < 1:
            return False
        
        if self._GetSize() >= count:
            self._UnsetMoveNext()

            self._SetCurrent(Enumerate(self._GetEnumerator().AsIterator()))

            return True
        
        return self._Enumerate()

class ResumableBufferedBatchEnumerator[T](ResumableBatchEnumeratorAbstract[T]):
    def __init__(self, size: int, enumerator: IEnumerator[T]) -> None:
        super().__init__()

        self.__size: int = size
        self.__source: IEnumerator[T] = enumerator

        self.__buffer: IList[T] = List[T]()
        self.__batchStart: IDoublyLinkedNode[T]|None = None
        self.__cursor: IDoublyLinkedNode[T]|None = None

        self.__moveNext: Function[bool] = self.__MoveNext

    @final
    def __TryGetCursor(self) -> IDoublyLinkedNode[T]|None:
        cursor: IDoublyLinkedNode[T]|None = self.__cursor

        return (self.__buffer.AddLast(self.__source.GetCurrent()) if self.__source.MoveNext() else None) if cursor is None else cursor

    @final
    def __Enumerate(self) -> Generator[T]:
        count: int = 0
        size: int = self._GetSize()
        node: IDoublyLinkedNode[T]|None = None

        while count < size:
            if (node := self.__TryGetCursor()) is None:
                return
            
            self.__cursor = node.GetNext()
            
            count += 1
            
            yield node.GetValue()
    
    @final
    def __MoveNext(self) -> bool:
        def completeBatch() -> None:
            if self.__batchStart is None:
                return
            
            _CompleteBatch(self.GetCurrent())
        
        def commit() -> None:
            if self.__batchStart is None:
                return

            if self.__cursor is None:
                self.__buffer.Clear()
            
            else:
                self.__cursor.RemoveRangeBefore()
        
        completeBatch()
        commit()

        node: IDoublyLinkedNode[T]|None = self.__TryGetCursor()

        if node is None:
            return False

        self.__cursor = node
        self.__batchStart = node

        self._SetCurrent(self.__Enumerate())

        return True

    @final
    def _GetSize(self) -> int:
        return self.__size

    @final
    def _GetSource(self) -> IEnumerator[T]:
        return self.__source

    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()

    @final
    def _TryResumeOverride(self, size: int) -> bool|None:
        def moveNext() -> bool:
            self._SetCurrent(self.__Enumerate())

            self.__moveNext = self.__MoveNext

            return True
        
        batchStart: IDoublyLinkedNode[T]|None = self.__batchStart

        if batchStart is None:
            return False
        
        self.__cursor = batchStart
        self.__size = size

        self.__moveNext = moveNext

        return True

    def _ResetOverride(self) -> bool:
        if self.__source.TryReset() is True:
            self.__buffer.Clear()

            self.__cursor = None
            self.__batchStart = None
            
            self.__moveNext = self.__MoveNext

            return True
        
        return False

    def _OnStopped(self) -> None:
        pass

    def _OnEnded(self) -> None:
        self.__moveNext = BoolFalse

        self.__buffer.Clear()

        self.__cursor = None
        self.__batchStart = None
        
        super()._OnEnded()

    def IsResetSupported(self) -> bool:
        return self.__source.IsResetSupported()

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

def TryBatch[T](items: IReadOnlyCountableIndexable[T]|ICountableEnumerable[T]|IEnumerable[T]|Sequence[T]|Collection[T]|Iterable[T]|None, size: int, safe: bool = True) -> Generator[Generator[T]]|None:
    def tryCreateEnumerator(items: IEnumerable[T]) -> IBatchEnumerator[T]|None:
        enumerator: IEnumerator[T]|None = items.TryGetEnumerator()

        return None if enumerator is None else BufferedBatchEnumerator[T](size, enumerator, safe)

    def batch(items: IReadOnlyCountableIndexable[T]|ICountableEnumerable[T]|IEnumerable[T]|Sequence[T]|Collection[T]|Iterable[T]) -> IBatchEnumerator[T]|None:
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
    
    if items is None:
        return None
    
    enumerator: IBatchEnumerator[T]|None = batch(items)

    return None if enumerator is None else Enumerate(enumerator.AsIterator())
def Batch[T](items: IReadOnlyCountableIndexable[T]|ICountableEnumerable[T]|IEnumerable[T]|Sequence[T]|Collection[T]|Iterable[T]|None, size: int, safe: bool = True) -> Generator[Generator[T]]:
    generator: Generator[Generator[T]]|None = TryBatch(items, size, safe)

    return MakeGenerator() if generator is None else generator