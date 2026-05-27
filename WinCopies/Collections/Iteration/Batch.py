from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Collection, Sequence
from typing import Callable, final

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Core import IReadOnlyCountableIndexable
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ICountableEnumerable, NullableEnumerator, AbstractEnumeratorBase, CreateIterable
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerable, IResumableCountableEnumerable, IResumableEnumerator as IResumableEnumeratorAbstract, IResumableEnumerationCursor
from WinCopies.Collections.Iteration import ForEach, Select
from WinCopies.Collections.Iteration.AdaptiveRefinement import IAdaptiveRefinement
from WinCopies.Collections.Linked.Doubly import IList, List, IDoublyLinkedNode
from WinCopies.Collections.Util import Enumerate, MakeGenerator
from WinCopies.Delegates import BoolFalse
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Action, Function, Converter, IFunction, IStruct, ValueFunction, Struct
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

type BatchGenerator[T] = Generator[Generator[T]]

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

class ICursor(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsValid(self) -> bool:
        pass

    @abstractmethod
    def TryResume(self, newSize: int|None = None) -> bool|None:
        pass

class ICompletionHandler(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def OnCompleted(self, size: int|None, safe: bool) -> None:
        pass
class IHandler(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Initialize(self, cursor: ICursor) -> None:
        pass

    @abstractmethod
    def CreateAdaptiveRefinement(self, size: int) -> IAdaptiveRefinement:
        pass

    @abstractmethod
    def GetCompletionHandler(self) -> ICompletionHandler:
        pass

class IResumableEnumeratorBase[T](IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def TryResume(self) -> bool:
        pass

class IResumableEnumerator[T](IResumableEnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def CanResume(self) -> bool:
        pass
    
    @abstractmethod
    def TryResume(self) -> bool:
        pass
class ResumableEnumerator[T](NullableEnumerator[T], IResumableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _TryResumeOverride(self) -> bool:
        pass
    
    def CanResume(self) -> bool:
        return self.IsStarted()
    
    @final
    def TryResume(self) -> bool:
        if self.CanResume():
            result: bool = self._TryResumeOverride()

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
    def __init__(self, size: IFunction[int], count: int) -> None:
        super().__init__()

        self.__start: int = 0
        self.__count: int = count

        self.__batchStart: int | None = None
        self.__size: IFunction[int] = size
    
    def _MoveNextOverride(self) -> bool:
        start: int = self.GetCurrentBatchIndex()
        count: int = self.GetCount()
        
        if start >= count:
            return False
        
        size: int = self.GetSize()
        end:  int = min(start + size, count)
        
        self.__batchStart = start
        self.__start = end
        
        self._SetCurrent(_GetCustomRange(start, end))
        
        return True
    
    @final
    def _TryResumeOverride(self) -> bool:
        batchStart: int|None = self.GetValidatedBatchIndex()

        if batchStart is None:
            return False

        self.__start = batchStart

        return True
    
    def _ResetOverride(self) -> bool:
        self.__start = 0
        self.__batchStart = None

        return True
    
    def _OnStopped(self) -> None:
        pass
    
    def IsResetSupported(self) -> bool:
        return True
    
    @final
    def GetValidatedBatchIndex(self) -> int|None:
        return self.__batchStart
    @final
    def GetCurrentBatchIndex(self) -> int:
        return self.__start
    @final
    def GetCount(self) -> int:
        return self.__count
    
    @final
    def GetSize(self) -> int:
        return self.__size.GetValue()

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
    def __init__(self, size: IFunction[int]) -> None:
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
    
    def _TryResumeOverride(self) -> bool:
        return self.__rangeEnumerator.TryResume()
    
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
    def __init__(self, size: IFunction[int], items: IReadOnlyCountableIndexable[T]) -> None:
        super().__init__(size)

        self.__items: IReadOnlyCountableIndexable[T] = items
    
    @final
    def _GetCount(self) -> int:
        return self.__items.GetCount()
    
    @final
    def _GetAt(self, index: int) -> T:
        return self.__items.GetAt(index)
class SequenceBatchEnumerator[T](IndexableBatchEnumeratorBase[T]):
    def __init__(self, size: IFunction[int], items: Sequence[T]) -> None:
        super().__init__(size)

        self.__items: Sequence[T] = items
    
    @final
    def _GetCount(self) -> int:
        return len(self.__items)
    
    @final
    def _GetAt(self, index: int) -> T:
        return self.__items[index]

class IResumableBatchInnerEnumerator[T](IResumableEnumeratorBase[Generator[T]]):
    def __init__(self) -> None:
        super().__init__()

class _ResumableBatchInnerEnumeratorBase[T](AbstractEnumeratorBase[T, Generator[T], IResumableEnumeratorAbstract[T]], IResumableBatchInnerEnumerator[T], IGenericConstraintImplementation[IResumableEnumeratorAbstract[T]]):
    def __init__(self, size: IFunction[int], enumerator: IResumableEnumeratorAbstract[T]) -> None:
        super().__init__(enumerator)

        self.__current: Generator[T]|None = None
        self.__cursor: IResumableEnumerationCursor|None = None
        
        self.__size: IFunction[int] = size
        
        self.__moveNext: Function[bool] = self.__MoveFirst
    
    @final
    def _GetSize(self) -> IFunction[int]:
        return self.__size
    
    @final
    def _SetCurrent(self, generator: Generator[T]) -> None:
        self.__current = generator
    
    @final
    def _PlaceCursor(self, enumerator: IResumableEnumeratorAbstract[T]) -> None:
        self.__cursor = enumerator.PlaceCursor()
    
    @abstractmethod
    def _MoveFirst(self, enumerator: IResumableEnumeratorAbstract[T]) -> bool:
        pass
    
    @final
    def _SetCurrentDefault(self, enumerator: IResumableEnumeratorAbstract[T]) -> None:
        def enumerate() -> Generator[T]:
            getCurrent: Function[T]

            def __getCurrent() -> T:
                return enumerator.GetCurrent()
            def _getCurrent() -> T:
                nonlocal getCurrent
                
                self._PlaceCursor(enumerator)

                return (getCurrent := __getCurrent)()

            getCurrent = _getCurrent
            
            for _ in _GetDefaultRange(self._GetSize().GetValue()):
                if enumerator.MoveNext():
                    yield getCurrent()
                
                else:
                    break
        
        self._SetCurrent(enumerate())
        
    @final
    def __MoveNext(self, enumerator: IResumableEnumeratorAbstract[T]) -> None:
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

        enumerator: IResumableEnumeratorAbstract[T] = self._GetContainer()

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
    
    def TryResume(self) -> bool:
        cursor: IResumableEnumerationCursor|None = self.__cursor

        if cursor is None:
            return False
        
        cursor.Resume()

        return True

@final
class _ResumableBatchInnerEnumerator[T](_ResumableBatchInnerEnumeratorBase[T]):
    def __init__(self, size: IFunction[int], enumerator: IResumableEnumeratorAbstract[T]) -> None:
        super().__init__(size, enumerator)
    
    def _MoveFirst(self, enumerator: IResumableEnumeratorAbstract[T]) -> bool:
        self._SetCurrentDefault(enumerator)
        
        return True
@final
class _ResumableBatchSafeInnerEnumerator[T](_ResumableBatchInnerEnumeratorBase[T]):
    def __init__(self, size: IFunction[int], enumerator: IResumableEnumeratorAbstract[T]) -> None:
        super().__init__(size, enumerator)
    
    def _MoveFirst(self, enumerator: IResumableEnumeratorAbstract[T]) -> bool:
        if enumerator.MoveNext():
            self._SetCurrent(_Enumerate(enumerator, self._GetSize().GetValue()))
            
            self._PlaceCursor(enumerator)

            return True
        
        return False

class ResumableBatchEnumeratorBase[TItem, TEnumerable](ResumableBatchEnumeratorAbstract[TItem], GenericConstraint[TEnumerable, IResumableEnumerable[TItem]]):
    def __init__(self, size: IFunction[int], items: TEnumerable) -> None:
        super().__init__()

        self.__items: TEnumerable = items
        self.__size: IFunction[int] = size

        self.__moveNext: Function[bool] = self._MoveNext
        self.__tryResume: Function[bool] = BoolFalse
    
    def _CreateEnumerator(self, size: IFunction[int], enumerator: IResumableEnumeratorAbstract[TItem]) -> IResumableBatchInnerEnumerator[TItem]:
        return _ResumableBatchInnerEnumerator[TItem](size, enumerator)
    
    @final
    def _Enumerate(self) -> bool:
        def tryGetEnumerator(size: IFunction[int]) -> IResumableBatchInnerEnumerator[TItem]|None:
            enumerator: IResumableEnumeratorAbstract[TItem]|None = items.TryGetResumableEnumerator()

            return None if enumerator is None else self._CreateEnumerator(size, enumerator)
        
        def moveNext(enumerator: IResumableBatchInnerEnumerator[TItem]) -> bool:
            if enumerator.MoveNext():
                self._SetCurrent(enumerator.GetCurrent())

                return True
            
            return False
        
        items: IResumableEnumerable[TItem] = self._GetInnerContainer()
        size: IFunction[int] = self._GetSize()

        enumerator: IResumableBatchInnerEnumerator[TItem]|None = tryGetEnumerator(size)

        if enumerator is None:
            return False

        self.__moveNext = lambda: moveNext(enumerator)
        self.__tryResume = enumerator.TryResume

        return self.__moveNext()
    
    @final
    def _GetContainer(self) -> TEnumerable:
        return self.__items
    
    @final
    def _GetSize(self) -> IFunction[int]:
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
    def _SetTryResume(self, func: Function[bool]) -> None:
        self.__tryResume = func
    
    def _TryResumeOverride(self) -> bool:
        return self.__tryResume()
    
    def _ResetOverride(self) -> bool:
        self.__moveNext = self._MoveNext
        self.__tryResume = BoolFalse

        return True
    
    def _OnStopped(self) -> None:
        pass
    
    def _OnEnded(self) -> None:
        self.__moveNext = BoolFalse
        self.__tryResume = BoolFalse

        super()._OnEnded()
    
    def IsResetSupported(self) -> bool:
        return True

class ResumableBatchEnumerator[T](ResumableBatchEnumeratorBase[T, IResumableEnumerable[T]], IGenericConstraintImplementation[IResumableEnumerable[T]]):
    def __init__(self, size: IFunction[int], items: IResumableEnumerable[T], safe: bool = True) -> None:
        super().__init__(size, items)

        self.__createEnumerator: Callable[[IFunction[int], IResumableEnumeratorAbstract[T]], IResumableBatchInnerEnumerator[T]] = self._CreateSafeEnumerator if safe else self._CreateUnsafeEnumerator
    
    def _CreateEnumerator(self, size: IFunction[int], enumerator: IResumableEnumeratorAbstract[T]) -> IResumableBatchInnerEnumerator[T]:
        return self.__createEnumerator(size, enumerator)
    
    @final
    def _CreateSafeEnumerator(self, size: IFunction[int], enumerator: IResumableEnumeratorAbstract[T]) -> IResumableBatchInnerEnumerator[T]:
        return _ResumableBatchSafeInnerEnumerator[T](size, enumerator)
    @final
    def _CreateUnsafeEnumerator(self, size: IFunction[int], enumerator: IResumableEnumeratorAbstract[T]) -> IResumableBatchInnerEnumerator[T]:
        return super()._CreateEnumerator(size, enumerator)
    
    def _MoveNext(self) -> bool:
        return self._Enumerate()
class ResumableCountableBatchEnumerator[T](ResumableBatchEnumeratorBase[T, IResumableCountableEnumerable[T]], IGenericConstraintImplementation[IResumableCountableEnumerable[T]]):
    def __init__(self, size: IFunction[int], items: IResumableCountableEnumerable[T]) -> None:
        super().__init__(size, items)
    
    def _MoveNext(self) -> bool:
        def tryResume() -> bool:
            self._SetMoveNext(self._MoveNext)

            return True

        count: int = self._GetCount()

        if count < 1:
            return False
        
        items: IResumableCountableEnumerable[T] = self._GetContainer()
        size: int = self._GetSize().GetValue()
        
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
    def __init__(self, size: IFunction[int], enumerator: IEnumerator[T]) -> None:
        super().__init__()

        self.__size: IFunction[int] = size
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
        size: int = self._GetSize().GetValue()
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
    def _GetSize(self) -> IFunction[int]:
        return self.__size

    @final
    def _GetSource(self) -> IEnumerator[T]:
        return self.__source

    def _MoveNextOverride(self) -> bool:
        return self.__moveNext()

    @final
    def _TryResumeOverride(self) -> bool:
        def moveNext() -> bool:
            self._SetCurrent(self.__Enumerate())

            self.__moveNext = self.__MoveNext

            return True
        
        batchStart: IDoublyLinkedNode[T]|None = self.__batchStart

        if batchStart is None:
            return False
        
        self.__cursor = batchStart
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

@final
class _Cursor[T](Abstract, ICursor):
    def __init__(self, size: IStruct[int], enumerator: IResumableBatchEnumerator[T], refinement: IAdaptiveRefinement, onResume: Action) -> None:
        super().__init__()

        self.__size: IStruct[int] = size
        self.__enumerator: IResumableBatchEnumerator[T] = enumerator
        self.__refinement: IAdaptiveRefinement = refinement
        self.__onResume: Action = onResume
    
    def IsValid(self) -> bool:
        return self.__enumerator.CanResume()
    
    def TryResume(self, newSize: int|None = None) -> bool|None:
        self.__onResume()

        if self.IsValid():
            refinement: IAdaptiveRefinement = self.__refinement

            if newSize is None:
                result: bool|None = refinement.TryOnError()

                if result is not True:
                    return result
            
            else:
                refinement.ResetTo(newSize, True)

            if self.__enumerator.TryResume():
                self.__size.SetValue(refinement.GetCurrent())

                return True
        
        return False

def TryBatch[T](size: int,
                items: IReadOnlyCountableIndexable[T]|IResumableCountableEnumerable[T]|IResumableEnumerable[T]|ICountableEnumerable[T]|IEnumerable[T]|Sequence[T]|Collection[T]|Iterable[T]|None,
                safe: bool = True, handler: IHandler|None = None) -> BatchGenerator[T]|None:
    def batch(items: IReadOnlyCountableIndexable[T]|IResumableCountableEnumerable[T]|IResumableEnumerable[T]|ICountableEnumerable[T]|IEnumerable[T]|Sequence[T]|Collection[T]|Iterable[T]) -> BatchGenerator[T]|None:
        def enumerate(enumerator: IBatchEnumerator[T]) -> BatchGenerator[T]:
            return Enumerate(enumerator.AsIterator())
        
        def createSizeStruct(size: int) -> IStruct[int]:
            return Struct[int](size)
        
        def handle(size: IStruct[int], enumerator: IResumableBatchEnumerator[T], handler: IHandler) -> BatchGenerator[T]:
            clean: bool = True

            def onError() -> None:
                nonlocal clean
                
                clean = False

            def onAdvance() -> None:
                nonlocal clean
                
                if clean and refinement.TryOnSuccess():
                    size.SetValue(refinement.GetCurrent())
                
                clean = True
            
            def enumerate() -> BatchGenerator[T]:
                try:
                    for batch in ForEach(enumerator.AsIterator(), onAdvance):
                        yield batch
                
                finally:
                    try:
                        handler.GetCompletionHandler().OnCompleted(refinement.GetDiscoveredSize(), refinement.IsTrueSize())
                    
                    finally:
                        enumerator.Stop()
            
            refinement: IAdaptiveRefinement = handler.CreateAdaptiveRefinement(size.GetValue())
            cursor: _Cursor[T] = _Cursor[T](size, enumerator, refinement, onError)

            handler.Initialize(cursor)

            return enumerate()
        def _handle(enumerator: IEnumerator[T], handler: IHandler) -> BatchGenerator[T]:
            _size: IStruct[int] = createSizeStruct(size)

            return handle(_size, ResumableBufferedBatchEnumerator[T](_size.AsFunction(), enumerator), handler)
        
        def tryHandle(selector: Converter[IFunction[int], IResumableBatchEnumerator[T]]) -> BatchGenerator[T]:
            if handler is None:
                return enumerate(selector(ValueFunction[int](size)))
            
            _size: IStruct[int] = createSizeStruct(size)

            return handle(_size, selector(_size.AsFunction()), handler)
        
        def tryCreateEnumerator(items: IEnumerable[T]) -> BatchGenerator[T]|None:
            enumerator: IEnumerator[T]|None = items.TryGetEnumerator()

            return None if enumerator is None else (enumerate(BufferedBatchEnumerator[T](size, enumerator, safe)) if handler is None else _handle(enumerator, handler))

        match items:
            case IReadOnlyCountableIndexable():
                return tryHandle(lambda size: IndexableBatchEnumerator[T](size, items))
            case Sequence():
                return tryHandle(lambda size: SequenceBatchEnumerator[T](size, items))
            
            case IResumableCountableEnumerable():
                return tryHandle(lambda size: ResumableCountableBatchEnumerator[T](size, items))
            case IResumableEnumerable():
                return tryHandle(lambda size: ResumableBatchEnumerator[T](size, items, safe))
            
            case ICountableEnumerable():
                if handler is None:
                    return enumerate(BufferedCountableBatchEnumerator[T](size, items))
                
                enumerator: IEnumerator[T]|None = items.TryGetEnumerator()

                return None if enumerator is None else _handle(enumerator, handler)
            case Collection():
                return enumerate(BufferedCollectionBatchEnumerator[T](size, items)) if handler is None else _handle(CreateIterable(items).GetEnumerator(), handler)
            
            case IEnumerable():
                return tryCreateEnumerator(items)
            case _:
                return tryCreateEnumerator(CreateIterable(items))
    
    return None if items is None else batch(items)
def Batch[T](size: int,
             items: IReadOnlyCountableIndexable[T]|IResumableCountableEnumerable[T]|IResumableEnumerable[T]|ICountableEnumerable[T]|IEnumerable[T]|Sequence[T]|Collection[T]|Iterable[T]|None,
             safe: bool = True, handler: IHandler|None = None) -> BatchGenerator[T]:
    generator: BatchGenerator[T]|None = TryBatch(size, items, safe, handler)

    return MakeGenerator() if generator is None else generator