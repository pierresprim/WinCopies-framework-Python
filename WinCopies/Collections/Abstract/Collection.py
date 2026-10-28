from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase, MutableSequence as MutableSequenceBase, Sized
from typing import final, overload, Self, SupportsIndex

from WinCopies import IInterface, IStringable, Abstract

from WinCopies.Collections import DuplicateKeyError
from WinCopies.Collections.Abstract.Enumeration import ResumableEnumerableAbstract
from WinCopies.Collections.Abstract.Monitor import CollectionViewMonitor, EquatableCollectionViewMonitor
from WinCopies.Collections.Abstract.Selection import StringableConverter, StringableTwoWayConverter
from WinCopies.Collections.Abstraction.Collection import GetTuple, GetEquatableTuple, GetHashableTuple, GetArray, GetList
from WinCopies.Collections.Abstraction.Selection.Enumeration import CreateCountableEnumerable
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration.Core import ICountableEnumerable, IEnumerator, CountableEnumerable, Enumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import (ICollectionViewMonitor, IEquatableCollectionViewMonitor,
                                              ICollectionMonitors,
                                              IReadOnlyLinkedCursorProvider, ILinkedCursorProvider,
                                              ITuple, IEquatableTuple, IHashableTuple,
                                              IArray, IList,
                                              Sequence, MutableSequence,
                                              GetViewString, AreTuplesEqual, GetTupleHash)
from WinCopies.Collections.Extensions.Collection import CollectionBase, ITupleBase, TupleAbstract as _TupleAbstract, TupleCollectionBase, EquatableTupleCollectionBase, HashableTupleCollectionBase, ArrayList
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Singly import (IReadOnlyCountableEnumerableList, ICountableEnumerableList,
                                                 IReadOnlyCountableEnumerableQueue, IReadOnlyCountableEnumerableStack,
                                                 ICountableEnumerableQueue, ICountableEnumerableStack)
from WinCopies.Collections.Range import SetItems
from WinCopies.Collections.Util import GetSequenceIndex, GetDuplicateItemError, GetDuplicateRangeError

from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Method, Converter, IndexedValueAction, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation

@final
class _Generator[T](Enumerator[T]):
    def __init__(self, items: ICountableEnumerableList[T]) -> None:
        super().__init__()

        self.__items: ICountableEnumerableList[T] = items

    def IsResetSupported(self) -> bool: return False

    def _MoveNextOverride(self) -> bool:
        result: INullable[T] = self.__items.TryPop()

        if result.HasValue():
            self._SetCurrent(result.GetValue())

            return True

        return False

    def _ResetOverride(self) -> bool: return False
@final
class _GeneratorProvider[T](Abstract, CountableEnumerable[T]):
    def __init__(self, items: ICountableEnumerableList[T]) -> None:
        super().__init__()

        self.__items: ICountableEnumerableList[T] = items

    def IsResumable(self) -> bool|None: return False

    def GetCount(self) -> int: return self.__items.GetCount()

    def TryGetEnumerator(self) -> IEnumerator[T]|None: return _Generator[T](self.__items)

class _ReadOnlyBufferSourceBase[TIn, TOut, TCollectionIn, TCollectionOut](Abstract):
    def __init__(self, source: TCollectionIn, items: TCollectionOut, converter: Converter[TIn, TOut]) -> None:
        super().__init__()

        self.__source: TCollectionIn = source
        self.__items: TCollectionOut = items
        self.__converter: Converter[TIn, TOut] = converter

    @final
    def _GetConverter(self) -> Converter[TIn, TOut]:
        return self.__converter

    @final
    def GetSource(self) -> TCollectionIn:
        return self.__source
    @final
    def GetItems(self) -> TCollectionOut:
        return self.__items
    
    @final
    def Convert(self, item: TIn) -> TOut:
        return self._GetConverter()(item)

@final
class _ReadOnlyBufferSource[TIn, TOut](_ReadOnlyBufferSourceBase[TIn, TOut, ITuple[TIn], ITuple[TOut]]):
    def __init__(self, source: ITuple[TIn], items: ITuple[TOut], selector: Converter[TIn, TOut]) -> None: super().__init__(source, items, selector)
@final
class _BufferSource[TIn, TOut](_ReadOnlyBufferSourceBase[TIn, TOut, IList[TIn], IList[TOut]]):
    def __init__(self, source: IList[TIn], items: IList[TOut], selector: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]) -> None:
        super().__init__(source, items, selector)

        self.__backConverter: Converter[TOut, TIn] = backConverter
    
    def ConvertBack(self, item: TOut) -> TIn:
        return self.__backConverter(item)

    def ToReadOnly(self) -> _ReadOnlyBufferSource[TIn, TOut]:
        return _ReadOnlyBufferSource[TIn, TOut](self.GetSource(), self.GetItems(), self._GetConverter())

class _IReadOnlyBuffer[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _AsReadOnlyCursor(self, source: ITuple[T]) -> IReadOnlyCountableEnumerableList[T]:
        ...

class _IReadOnlyBufferedQueue[T](_IReadOnlyBuffer[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsReadOnlyCursor(self, source: ITuple[T]) -> IReadOnlyCountableEnumerableList[T]: return source.AsQueuedCursor()
class _IReadOnlyBufferedStack[T](_IReadOnlyBuffer[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsReadOnlyCursor(self, source: ITuple[T]) -> IReadOnlyCountableEnumerableList[T]: return source.AsStackedCursor()

class _ReadOnlyBufferBase[TIn, TOut, TCollectionIn, TCollectionOut, TBufferSource](Abstract, IReadOnlyCountableEnumerableList[TOut], _IReadOnlyBuffer[TIn]):
    def __init__(self, bufferSource: TBufferSource) -> None:
        super().__init__()

        self.__bufferSource: TBufferSource = bufferSource

    @abstractmethod
    def _AsTupleIn(self, items: TCollectionIn) -> ITuple[TIn]:
        ...
    @abstractmethod
    def _AsTupleOut(self, items: TCollectionOut) -> ITuple[TOut]:
        ...

    @abstractmethod
    def _AsBufferSource(self, items: TBufferSource) -> _ReadOnlyBufferSourceBase[TIn, TOut, TCollectionIn, TCollectionOut]:
        ...

    @final
    def _GetBufferSource(self) -> TBufferSource:
        return self.__bufferSource
    @final
    def __GetBufferSource(self) -> _ReadOnlyBufferSourceBase[TIn, TOut, TCollectionIn, TCollectionOut]:
        return self._AsBufferSource(self._GetBufferSource())

    @final
    def __GetSource(self) -> ITuple[TIn]: return self._AsTupleIn(self._GetSource())
    @final
    def __GetItems(self) -> ITuple[TOut]: return self._AsTupleOut(self.__GetBufferSource().GetItems())

    @final
    def _GetSource(self) -> TCollectionIn:
        return self.__GetBufferSource().GetSource()
    
    @final
    def _Convert(self, item: INullable[TIn]) -> INullable[TOut]:
        return GetNullable(self.__GetBufferSource().Convert(item.GetValue())) if item.HasValue() else GetNullValue()

    @final
    def IsEmpty(self) -> bool: return self.__GetSource().IsEmpty()

    @final
    def GetCount(self) -> int: return self.__GetSource().GetCount()

    @final
    def TryPeek(self) -> INullable[TOut]: return self._Convert(self._AsReadOnlyCursor(self.__GetSource()).TryPeek())
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TOut]|None: return self.__GetItems().TryGetEnumerator()

    @final
    def AsSized(self) -> Sized: return self.__GetSource().AsReadOnly().AsSized()
    @final
    def AsIterable(self) -> Iterable[TOut]: return self.__GetItems().AsIterable()

class _ReadOnlyBuffer[TIn, TOut](_ReadOnlyBufferBase[TIn, TOut, ITuple[TIn], ITuple[TOut], _ReadOnlyBufferSource[TIn, TOut]], IReadOnlyCountableEnumerableList[TOut]):
    def __init__(self, bufferSource: _ReadOnlyBufferSource[TIn, TOut]) -> None: super().__init__(bufferSource)

    @final
    def _AsTupleIn(self, items: ITuple[TIn]) -> ITuple[TIn]: return items
    @final
    def _AsTupleOut(self, items: ITuple[TOut]) -> ITuple[TOut]: return items

    @final
    def _AsBufferSource(self, items: _ReadOnlyBufferSource[TIn, TOut]) -> _ReadOnlyBufferSource[TIn, TOut]: return items
class _Buffer[TIn, TOut](_ReadOnlyBufferBase[TIn, TOut, IList[TIn], IList[TOut], _BufferSource[TIn, TOut]], ICountableEnumerableList[TOut]):
    def __init__(self, bufferSource: _BufferSource[TIn, TOut]) -> None: super().__init__(bufferSource)

    @final
    def _AsTupleIn(self, items: IList[TIn]) -> ITuple[TIn]: return items
    @final
    def _AsTupleOut(self, items: IList[TOut]) -> ITuple[TOut]: return items

    @final
    def _AsBufferSource(self, items: _BufferSource[TIn, TOut]) -> _BufferSource[TIn, TOut]: return items

    @abstractmethod
    def _AsCursor(self, source: IList[TIn]) -> ICountableEnumerableList[TIn]:
        ...
    @final
    def __AsCursor(self) -> ICountableEnumerableList[TIn]:
        return self._AsCursor(self._GetSource())

    @final
    def __Push(self, items: Iterable[TOut], selector: Converter[ICountableEnumerableList[TIn], Method[Iterable[TIn]]]) -> None: selector(self.__AsCursor())(Select(items, self._GetBufferSource().ConvertBack))

    @final
    def Push(self, value: TOut) -> None: self.__AsCursor().Push(self._GetBufferSource().ConvertBack(value))
    @final
    def PushItems(self, items: Iterable[TOut]) -> None: self.__Push(items, lambda cursor: cursor.PushItems)
    @final
    def PushRange(self, items: Iterable[TOut]) -> None: self.__Push(items, lambda cursor: cursor.PushRange)
    
    @final
    def TryPop(self) -> INullable[TOut]: return self._Convert(self.__AsCursor().TryPop())

    @final
    def Clear(self) -> None: self.__AsCursor().Clear()

    @final
    def AsCountableGenerator(self) -> ICountableEnumerable[TOut]: return _GeneratorProvider[TOut](self)

@final
class _ReadOnlyBufferedQueue[TIn, TOut](_ReadOnlyBuffer[TIn, TOut], IReadOnlyCountableEnumerableQueue[TOut], _IReadOnlyBufferedQueue[TIn]):
    def __init__(self, bufferSource: _ReadOnlyBufferSource[TIn, TOut]) -> None: super().__init__(bufferSource)
@final
class _ReadOnlyBufferedStack[TIn, TOut](_ReadOnlyBuffer[TIn, TOut], IReadOnlyCountableEnumerableStack[TOut], _IReadOnlyBufferedStack[TIn]):
    def __init__(self, bufferSource: _ReadOnlyBufferSource[TIn, TOut]) -> None: super().__init__(bufferSource)

@final
class _BufferedQueue[TIn, TOut](_Buffer[TIn, TOut], ICountableEnumerableQueue[TOut], _IReadOnlyBufferedQueue[TIn]):
    def __init__(self, bufferSource: _BufferSource[TIn, TOut]) -> None:
        super().__init__(bufferSource)

        self.__readOnly: IReadOnlyCountableEnumerableQueue[TOut] = _ReadOnlyBufferedQueue[TIn, TOut](bufferSource.ToReadOnly())

    def _AsCursor(self, source: IList[TIn]) -> ICountableEnumerableList[TIn]: return source.AsQueuedCursor()

    def AsReadOnly(self) -> IReadOnlyCountableEnumerableQueue[TOut]: return self.__readOnly
@final
class _BufferedStack[TIn, TOut](_Buffer[TIn, TOut], ICountableEnumerableStack[TOut], _IReadOnlyBufferedStack[TIn]):
    def __init__(self, bufferSource: _BufferSource[TIn, TOut]) -> None:
        super().__init__(bufferSource)

        self.__readOnly: IReadOnlyCountableEnumerableStack[TOut] = _ReadOnlyBufferedStack[TIn, TOut](bufferSource.ToReadOnly())

    def _AsCursor(self, source: IList[TIn]) -> ICountableEnumerableList[TIn]: return source.AsStackedCursor()

    def AsReadOnly(self) -> IReadOnlyCountableEnumerableStack[TOut]: return self.__readOnly

@final
class _ReadOnlyBufferProvider[TIn, TOut](Abstract, IReadOnlyLinkedCursorProvider[TOut]):
    def __init__(self, bufferSource: _ReadOnlyBufferSource[TIn, TOut]) -> None:
        super().__init__()

        self.__queued: IReadOnlyCountableEnumerableQueue[TOut] = _ReadOnlyBufferedQueue[TIn, TOut](bufferSource)
        self.__stacked: IReadOnlyCountableEnumerableStack[TOut] = _ReadOnlyBufferedStack[TIn, TOut](bufferSource)

    def AsQueuedCursor(self) -> IReadOnlyCountableEnumerableQueue[TOut]: return self.__queued
    def AsStackedCursor(self) -> IReadOnlyCountableEnumerableStack[TOut]: return self.__stacked
@final
class _ReadOnlyBufferProviderUpdater[TIn, TOut](ValueFunctionUpdater[IReadOnlyLinkedCursorProvider[TOut]]):
    def __init__(self, bufferSource: _ReadOnlyBufferSource[TIn, TOut], updater: Method[IFunction[IReadOnlyLinkedCursorProvider[TOut]]]) -> None:
        super().__init__(updater)

        self.__bufferSource: _ReadOnlyBufferSource[TIn, TOut] = bufferSource

    def _GetValue(self) -> IReadOnlyLinkedCursorProvider[TOut]: return _ReadOnlyBufferProvider[TIn, TOut](self.__bufferSource)

@final
class _BufferProvider[TIn, TOut](Abstract, ILinkedCursorProvider[TOut]):
    def __init__(self, bufferSource: _BufferSource[TIn, TOut]) -> None:
        super().__init__()

        self.__queued: ICountableEnumerableQueue[TOut] = _BufferedQueue[TIn, TOut](bufferSource)
        self.__stacked: ICountableEnumerableStack[TOut] = _BufferedStack[TIn, TOut](bufferSource)

    def AsQueuedCursor(self) -> ICountableEnumerableQueue[TOut]: return self.__queued
    def AsStackedCursor(self) -> ICountableEnumerableStack[TOut]: return self.__stacked
@final
class _BufferProviderUpdater[TIn, TOut](ValueFunctionUpdater[ILinkedCursorProvider[TOut]]):
    def __init__(self, bufferSource: _BufferSource[TIn, TOut], updater: Method[IFunction[ILinkedCursorProvider[TOut]]]) -> None:
        super().__init__(updater)

        self.__bufferSource: _BufferSource[TIn, TOut] = bufferSource

    def _GetValue(self) -> ILinkedCursorProvider[TOut]: return _BufferProvider[TIn, TOut](self.__bufferSource)

class TupleCollectionAbstractBase[TIn, TOut, TSequence: IStringable](StringableConverter[TIn, TOut, TSequence, ITuple[TIn]], Sequence[TOut], _TupleAbstract[TOut], ResumableEnumerableAbstract[TIn, TOut]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _Clone(self, items: TSequence) -> Self:
        ...
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def _GetAt(self, key: int) -> TOut:
        return self._Convert(self._GetInnerContainer().GetAt(key))
    
    @final
    def Contains(self, value: TOut|object) -> bool: return any(item is value or item == value for item in self.AsIterable())
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None: return self._GetInnerContainer().TryGetEnumerator()
    @final
    def _TryGetResumableEnumerator(self) -> IResumableEnumerator[TIn]|None: return self._GetInnerContainer().TryGetResumableEnumerator()
    
    @final
    def ToString(self) -> str: return GetViewString(self, self._GetContainer())
class TupleCollectionAbstract[TIn, TOut, TSequence: IStringable](TupleCollectionAbstractBase[TIn, TOut, TSequence], ITupleBase[TOut]):
    def __init__(self) -> None: super().__init__()

class TupleAbstract[TIn, TOut, TSequence: IStringable](TupleCollectionAbstractBase[TIn, TOut, TSequence]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TOut: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TOut]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TOut|SequenceBase[TOut]: return self._Convert(self._GetInnerContainer().GetAt(GetSequenceIndex(index, self.GetCount()))) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()
class TupleBase[TIn, TOut, TSequence: IStringable](TupleAbstract[TIn, TOut, TSequence], ITupleBase[TOut]):
    def __init__(self) -> None: super().__init__()

class _IReadOnlyCursorProvider[TIn, TOut](IReadOnlyLinkedCursorProvider[TOut]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateCursorProvider(self, bufferSource: _ReadOnlyBufferSource[TIn, TOut], updater: Method[IFunction[IReadOnlyLinkedCursorProvider[TOut]]]) -> IFunction[IReadOnlyLinkedCursorProvider[TOut]]:
        return _ReadOnlyBufferProviderUpdater[TIn, TOut](bufferSource, updater)

    @abstractmethod
    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[TOut]]:
        ...
    @final
    def __GetCursorProvider(self) -> IReadOnlyLinkedCursorProvider[TOut]:
        return self._GetCursorProvider().GetValue()

    @final
    def AsQueuedCursor(self) -> IReadOnlyCountableEnumerableQueue[TOut]: return self.__GetCursorProvider().AsQueuedCursor()
    @final
    def AsStackedCursor(self) -> IReadOnlyCountableEnumerableStack[TOut]: return self.__GetCursorProvider().AsStackedCursor()
class _ICursorProvider[TIn, TOut](ILinkedCursorProvider[TOut]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateCursorProvider(self, bufferSource: _BufferSource[TIn, TOut], updater: Method[IFunction[ILinkedCursorProvider[TOut]]]) -> IFunction[ILinkedCursorProvider[TOut]]:
        return _BufferProviderUpdater[TIn, TOut](bufferSource, updater)

    @abstractmethod
    def _GetCursorProvider(self) -> IFunction[ILinkedCursorProvider[TOut]]:
        ...
    @final
    def __GetCursorProvider(self) -> ILinkedCursorProvider[TOut]:
        return self._GetCursorProvider().GetValue()

    @final
    def AsQueuedCursor(self) -> ICountableEnumerableQueue[TOut]: return self.__GetCursorProvider().AsQueuedCursor()
    @final
    def AsStackedCursor(self) -> ICountableEnumerableStack[TOut]: return self.__GetCursorProvider().AsStackedCursor()

class Tuple[TIn, TOut](TupleCollectionBase[TOut], TupleBase[TIn, TOut, ITuple[TIn]], _IReadOnlyCursorProvider[TIn, TOut], IGenericConstraintImplementation[ITuple[TIn]]):
    def __init__(self, items: ITuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        def update(func: IFunction[IReadOnlyLinkedCursorProvider[TOut]]) -> None: self.__cursorProvider = func
        
        super().__init__()

        self.__items: ITuple[TIn] = (items := GetTuple(items))
        self.__cursorProvider: IFunction[IReadOnlyLinkedCursorProvider[TOut]] = self._CreateCursorProvider(_ReadOnlyBufferSource[TIn, TOut](items, self, self._Convert), update) # type: ignore[no-redef]
        self.__monitor: ICollectionViewMonitor[TOut] = CollectionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[TOut]]: return self.__cursorProvider

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> ITuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return self.__items.GetSourceMutability()

    @final
    def AsReadOnly(self) -> ITuple[TOut]: return self
    
    @final
    def SliceAt(self, key: slice) -> ITuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
class EquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](EquatableTupleCollectionBase[TOut], TupleBase[TIn, TOut, IEquatableTuple[TIn]], _IReadOnlyCursorProvider[TIn, TOut], IGenericConstraintImplementation[IEquatableTuple[TIn]]):
    def __init__(self, items: IEquatableTuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        def update(func: IFunction[IReadOnlyLinkedCursorProvider[TOut]]) -> None: self.__cursorProvider = func
        
        super().__init__()

        self.__items: IEquatableTuple[TIn] = (items := GetEquatableTuple(items))
        self.__cursorProvider: IFunction[IReadOnlyLinkedCursorProvider[TOut]] = self._CreateCursorProvider(_ReadOnlyBufferSource[TIn, TOut](items, self, self._Convert), update) # type: ignore[no-redef]
        self.__monitor: IEquatableCollectionViewMonitor[TOut] = EquatableCollectionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[TOut]]: return self.__cursorProvider

    @final
    def _GetCollectionViewMonitor(self) -> IEquatableCollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IEquatableTuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return self.__items.GetSourceMutability()
    
    def Equals(self, item: object) -> bool: return AreTuplesEqual(self, item)
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

    @final
    def AsImmutable(self) -> IEquatableTuple[TOut]: return self._GetCollectionViewMonitor().GetImmutableView()
class HashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](HashableTupleCollectionBase[TOut], TupleAbstract[TIn, TOut, IHashableTuple[TIn]], _IReadOnlyCursorProvider[TIn, TOut], IGenericConstraintImplementation[IHashableTuple[TIn]]):
    def __init__(self, items: IHashableTuple[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        def update(func: IFunction[IReadOnlyLinkedCursorProvider[TOut]]) -> None: self.__cursorProvider = func

        super().__init__()

        self.__items: IHashableTuple[TIn] = (items := GetHashableTuple(items))
        self.__cursorProvider: IFunction[IReadOnlyLinkedCursorProvider[TOut]] = self._CreateCursorProvider(_ReadOnlyBufferSource[TIn, TOut](items, self, self._Convert), update) # type: ignore[no-redef]

    @final
    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[TOut]]: return self.__cursorProvider

    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IHashableTuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return self.__items.GetSourceMutability()
    
    def Equals(self, item: object) -> bool: return AreTuplesEqual(self, item)
    def Hash(self) -> int: return GetTupleHash(self)
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

class ArrayAbstract[TIn, TOut, TSequence: IStringable](TupleCollectionAbstract[TIn, TOut, TSequence], StringableTwoWayConverter[TIn, TOut, TSequence, ITuple[TIn]], GenericSpecializedConstraint[TSequence, ITuple[TIn], IArray[TIn]]):
    def __init__(self) -> None: super().__init__()

    # A converting layer hands the container the converted value, and the container refuses a value it
    # already holds in its own terms. A single write gives one value, which is then the one held: the
    # refusal is told again with the value as the caller gave it, the container's own kept as its cause.
    def _Write(self, write: IndexedValueAction[TIn], index: int, value: TOut) -> None:
        try: write(index, self._ConvertBack(value))

        except DuplicateKeyError as error:
            if error.GetDuplicate().HasValue(): raise GetDuplicateItemError(value) from error
            
            raise
    
    @final
    def _Move(self, x: int, y: int) -> None: self._GetSpecializedContainer().Move(x, y)
    @final
    def _Swap(self, x: int, y: int) -> None: self._GetSpecializedContainer().Swap(x, y)
    
    @final
    def _SetAt(self, key: int, value: TOut, throwOnError: bool) -> bool:
        items: IArray[TIn] = self._GetSpecializedContainer()

        if throwOnError:
            self._Write(items.SetAt, key, value)

            return True
        
        return items.TrySetAt(key, self._ConvertBack(value))

    @final
    def AsImmutable(self) -> ITuple[TOut]: return self._GetCollectionViewMonitor().GetImmutableView()
class ArrayBase[TIn, TOut, TSequence: IStringable](TupleBase[TIn, TOut, TSequence], ArrayAbstract[TIn, TOut, TSequence]):
    def __init__(self) -> None: super().__init__()

class Array[TIn, TOut](ArrayBase[TIn, TOut, IArray[TIn]], ArrayList[TOut], _IReadOnlyCursorProvider[TIn, TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IArray[TIn]]):
    def __init__(self, items: IArray[TIn]|Sequence[TIn]|Iterable[TIn]) -> None:
        def update(func: IFunction[IReadOnlyLinkedCursorProvider[TOut]]) -> None: self.__cursorProvider = func

        super().__init__()

        self.__items: IArray[TIn] = (items := GetArray(items))
        self.__cursorProvider: IFunction[IReadOnlyLinkedCursorProvider[TOut]] = self._CreateCursorProvider(_ReadOnlyBufferSource[TIn, TOut](items, self, self._Convert), update) # type: ignore[no-redef]
        self.__monitor: ICollectionViewMonitor[TOut] = CollectionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[TOut]]: return self.__cursorProvider

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IArray[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return self.__items.GetSourceMutability()
    
    @final
    def SliceAt(self, key: slice) -> IArray[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

class List[TIn, TOut](ArrayAbstract[TIn, TOut, IList[TIn]], CollectionBase[TOut], MutableSequence[TOut], _ICursorProvider[TIn, TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IList[TIn]]):
    def __init__(self, items: IList[TIn]|MutableSequence[TIn]|Iterable[TIn]) -> None:
        def update(func: IFunction[ILinkedCursorProvider[TOut]]) -> None: self.__cursorProvider = func

        super().__init__()

        self.__items: IList[TIn] = (items := GetList(items))
        self.__cursorProvider: IFunction[ILinkedCursorProvider[TOut]] = self._CreateCursorProvider(_BufferSource[TIn, TOut](items, self, self._Convert, self._ConvertBack), update) # type: ignore[no-redef]
        self.__monitor: ICollectionViewMonitor[TOut] = CollectionViewMonitor[TIn, TOut](items, self)

    @final
    def _GetCursorProvider(self) -> IFunction[ILinkedCursorProvider[TOut]]: return self.__cursorProvider

    @final
    def __Select(self, items: Iterable[TOut]|None) -> Iterable[TIn]:
        return Select(items, self._ConvertBack)

    @final
    def _GetCollectionViewMonitor(self) -> ICollectionViewMonitor[TOut]: return self.__monitor
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetContainer().GetCollectionMonitors()
    
    @final
    def _GetContainer(self) -> IList[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return self.__items.GetSourceMutability()
    
    @final
    def SliceAt(self, key: slice) -> IList[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
    
    @final
    def _TryInsert(self, index: int, value: TOut) -> bool: return self._GetContainer().TryInsert(index, self._ConvertBack(value))
    @final
    def _Insert(self, index: int, value: TOut) -> None: self._Write(self._GetContainer().Insert, index, value)
    @final
    def _TryInsertRange(self, index: int, items: Iterable[TOut]) -> bool: return self._GetContainer().TryInsertRange(index, self.__Select(items)) is True
    @final
    def _InsertRange(self, index: int, items: Iterable[TOut]) -> None: self._GetContainer().InsertRange(index, self.__Select(items))
    
    # Converted into a tuple rather than handed over as a projection: the container's answer
    # reads the items and its write reads them again, and a lazy Select would reach the first
    # reader only. The conversion is this layer's whole contribution -- whether the span may
    # be written is the inner container's to say, in its own vocabulary. A duplicate it refuses
    # names its own value, which this layer cannot tell again in the caller's: a span gives
    # several, and which of the two causes applies is the container's to know. So the refusal
    # names none, as a range refused as a whole does, the container's own kept as its cause.
    @final
    def CanSetRange(self, indices: ICountableEnumerable[int], items: ICountableEnumerable[TOut], throwOnError: bool = False) -> bool:
        try: return self._GetContainer().CanSetRange(indices, CreateCountableEnumerable(items, self._ConvertBack), throwOnError)
        
        except DuplicateKeyError as error:
            if error.GetDuplicate().HasValue(): raise GetDuplicateRangeError() from error

            raise
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None: return self._GetContainer().TryRemoveAt(index)
    @final
    def _RemoveRange(self, index: int, count: int) -> None: return self._GetContainer().RemoveRange(index, count)
    
    @final
    def Clear(self) -> None: self._GetContainer().Clear()
    
    @final
    def insert(self, index: int, value: TOut) -> None: self._Write(self._GetContainer().AsMutableSequence().insert, index, value)
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TOut: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[TOut]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TOut|MutableSequenceBase[TOut]: return self._Convert(self._GetInnerContainer().GetAt(GetSequenceIndex(index, self.GetCount()))) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsMutableSequence()
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: TOut) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TOut]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TOut|Iterable[TOut]) -> None: SetItems(self, index, value)
    
    @final
    def __delitem__(self, index: int|slice) -> None: del self._GetContainer().AsMutableSequence()[index]