from abc import abstractmethod
from typing import final

from WinCopies import IDisposable
from WinCopies.Collections import IReadOnlyCollection, IGetter
from WinCopies.Collections.Enumeration import IEnumerable, IEnumeratorBase, IEnumerator, EnumeratorBase, AbstractEnumeratorBase
from WinCopies.Collections.Generation import IResumable, INode
from WinCopies.Collections.Generation.Factory import IObjectFactory, DisposableObjectFactory
from WinCopies.Typing.Generic import IGenericConstraintImplementation

class IResumableEnumerationCursor(IResumable, IDisposable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def MoveToTop(self) -> None:
        pass

class IResumableEnumerator[T](IEnumerator[T], IDisposable):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def SupportsMultipleCursors(self) -> bool:
        pass
    
    @abstractmethod
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        pass
    @abstractmethod
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        pass

    @abstractmethod
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        pass

    @abstractmethod
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        pass

class IResumableEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None:
        pass

class ResumableEnumeratorBase[T](EnumeratorBase[T], IResumableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
class ResumableEnumerator[T](ResumableEnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

class IResumableEnumerationCursorFactory[T: IResumableEnumerationCursor](IObjectFactory[T], IGetter[int, T], IReadOnlyCollection):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def GetLastCursor(self) -> IResumableEnumerationCursor:
        pass
class ResumableEnumerationCursorFactory[T: IResumableEnumerationCursor](DisposableObjectFactory[T], IResumableEnumerationCursorFactory[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _InitializeCursor(self, cursor: T, node: INode) -> None:
        pass

    @abstractmethod
    def _AddItem(self, item: T) -> None:
        pass

    @abstractmethod
    def _Clear(self) -> None:
        pass
    
    def _Push(self, item: T) -> INode:
        node: INode = super()._Push(item)

        self._InitializeCursor(item, node)

        self._AddItem(item)

        return node
    
    def InvalidateObjects(self) -> None:
        super().InvalidateObjects()

        self._Clear()
    
    @final
    def GetLastCursor(self) -> T:
        return self._GetItems().GetLastValue()

class AbstractResumableEnumeratorAbstract[TIn, TOut, TEnumerator: IEnumeratorBase](AbstractEnumeratorBase[TIn, TOut, TEnumerator], IResumableEnumerator[TOut]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__(enumerator)
class AbstractResumableEnumeratorBase[TItem, TEnumerator: IEnumeratorBase](AbstractResumableEnumeratorAbstract[TItem, TItem, TEnumerator]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__(enumerator)
class AbstractResumableEnumerator[T](AbstractResumableEnumeratorBase[T, IResumableEnumerator[T]], IGenericConstraintImplementation[IResumableEnumerator[T]]):
    def __init__(self, enumerator: IResumableEnumerator[T]) -> None:
        super().__init__(enumerator)