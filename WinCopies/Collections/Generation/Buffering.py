from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Iteration import PrependValues, Select
from WinCopies.Collections.Util import MakeSequence
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method
from WinCopies.Typing.Generic import IGenericConstraint

class _BuilderNode[T](Abstract):
    def __init__(self, value: T) -> None:
        super().__init__()

        self.__value: T = value
        self.__next: _BuilderNode[T]|None = None

    @final
    def GetValue(self) -> T:
        return self.__value

    @final
    def SetNext(self, value: T) -> _BuilderNode[T]:
        next: _BuilderNode[T] = _BuilderNode[T](value)

        self.__next = next

        return next

    @final
    def RemoveNext(self) -> _BuilderNode[T]|None:
        next: _BuilderNode[T]|None = self.__next

        self.__next = None

        return next

type BuildResult[T] = tuple[T, Iterable[T]|None]

class IBuilderBase[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def HasItems(self) -> bool:
        ...

    @abstractmethod
    def Push(self, value: T) -> None:
        ...
class IBuilder[T](IBuilderBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Build(self) -> Iterable[T]|None:
        ...
    @abstractmethod
    def TryBuild(self) -> INullable[T]|Iterable[T]:
        ...
class Builder[T](Abstract, IBuilder[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__first: _BuilderNode[T]|None = None
        self.__last: _BuilderNode[T]|None = None

        self.__push: Method[T] = self.__Push

    @final
    def __Push(self, value: T) -> None:
        def push(value: T) -> None:
            last: _BuilderNode[T] = self.__last # type: ignore[assignment]

            self.__last = last.SetNext(value)

        first: _BuilderNode[T] = _BuilderNode[T](value)

        self.__first = first
        self.__last = first

        self.__push = push

    @final
    def __Build(self, includeFirst: bool) -> BuildResult[T]|None:
        def build(first: _BuilderNode[T]) -> BuildResult[T]:
            def build(node: _BuilderNode[T]|None) -> Generator[_BuilderNode[T]]:
                while node is not None:
                    yield node

                    node = node.RemoveNext()
            
            def makeSequence(nodes: Iterable[_BuilderNode[T]]) -> Iterable[T]:
                return Select(nodes, lambda node: node.GetValue())
            
            def createTuple(items: Iterable[T]|None) -> BuildResult[T]:
                return first.GetValue(), items

            next: _BuilderNode[T]|None = first.RemoveNext()

            return createTuple(makeSequence(MakeSequence(first)) if includeFirst else None) if next is None else createTuple(makeSequence(PrependValues(build(next.RemoveNext()), first, next)))
        
        first: _BuilderNode[T]|None = self.__first

        if first is None: return None

        self.__first = None
        self.__last = None

        self.__push = self.__Push

        return build(first)

    @final
    def HasItems(self) -> bool: return self.__first is not None

    @final
    def Push(self, value: T) -> None:
        self.__push(value)

    @final
    def Build(self) -> Iterable[T]|None:
        result: BuildResult[T]|None = self.__Build(True)

        return None if result is None else result[1]
    @final
    def TryBuild(self) -> INullable[T]|Iterable[T]:
        result: BuildResult[T]|None = self.__Build(False)

        if result is None: return GetNullValue()

        items: Iterable[T]|None = result[1]

        return GetNullable(result[0]) if items is None else items

class IAbstractionBuilder[TItem, TList](IBuilderBase[TItem]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Build(self) -> TList|None:
        ...
    @abstractmethod
    def TryBuild(self) -> INullable[TItem]|TList:
        ...
class AbstractionBuilder[TItem, TList](Abstract, IAbstractionBuilder[TItem, TList]):
    def __init__(self) -> None:
        super().__init__()

        self.__builder: IBuilder[TItem] = Builder[TItem]()

    @abstractmethod
    def _CreateList(self, items: Iterable[TItem]) -> TList:
        ...

    @final
    def _GetBuilder(self) -> IBuilder[TItem]:
        return self.__builder

    @final
    def HasItems(self) -> bool: return self._GetBuilder().HasItems()

    @final
    def Push(self, value: TItem) -> None: return self._GetBuilder().Push(value)

    @final
    def Build(self) -> TList|None:
        items: Iterable[TItem]|None = self._GetBuilder().Build()

        return None if items is None else self._CreateList(items)
    @final
    def TryBuild(self) -> INullable[TItem]|TList:
        result: INullable[TItem]|Iterable[TItem] = self._GetBuilder().TryBuild()

        return result if isinstance(result, INullable) else self._CreateList(result)

class IGroupBuilder[TItem, TList](IAbstractionBuilder[TItem, TList], IGenericConstraint[TList, TItem]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryBuildGroup(self) -> INullable[TItem]:
        ...
class GroupBuilder[TItem, TList](AbstractionBuilder[TItem, TList], IGroupBuilder[TItem, TList]):
    def __init__(self) -> None: super().__init__()

    @final
    def TryBuildGroup(self) -> INullable[TItem]:
        result: INullable[TItem]|Iterable[TItem] = self._GetBuilder().TryBuild()
        
        return result if isinstance(result, INullable) else GetNullable(self._AsContainer(self._CreateList(result)))