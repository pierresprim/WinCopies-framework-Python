from __future__ import annotations

from abc import abstractmethod
from typing import final



from WinCopies import Abstract

from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, AbstractEnumerator
from WinCopies.Collections.Enumeration.Recursive.Base import IRecursiveEnumerationHandlerBase, IRecursiveEnumerationDelegate, IRecursiveEnumerationCookie
from WinCopies.Collections.Enumeration.Recursive._Base import IRecursiveEnumeratorBase, IDelegate, Delegate, NullRecursiveEnumerationHandler, NullRecursiveEnumerationDelegate
from WinCopies.Collections.Linked.Singly import Stack

from WinCopies.Typing import InvalidOperationError, INullable

class RecursiveEnumeratorBase[TItem, TCookie, TStackItems](AbstractEnumerator[TItem], IRecursiveEnumeratorBase[TItem, TCookie, TStackItems]):
    @final
    class __Cookie[_TItem, _TCookie, _TStackItems](Abstract, IRecursiveEnumerationCookie[_TItem, _TCookie, _TStackItems]):
        def __init__(self, enumerator: RecursiveEnumeratorBase[_TItem, _TCookie, _TStackItems], delegate: IDelegate[_TItem]) -> None:
            super().__init__()

            self.__enumerator: RecursiveEnumeratorBase[_TItem, _TCookie, _TStackItems] = enumerator
            self.__delegate: IDelegate[_TItem] = delegate
            self.__enumerators: Stack[_TStackItems]|None = None
        
        def Initialize(self) -> None:
            self.__enumerators = Stack[_TStackItems]()

        def GetEnumerator(self) -> IEnumerator[_TItem]:
            return self.__delegate.GetEnumerator()
        
        def GetEnumerationItems(self, enumerationItems: _TItem) -> IEnumerable[_TItem]:
            return self.__delegate.GetEnumerationItems(enumerationItems)
        
        def MoveNext(self) -> bool:
            return self.__delegate.MoveNext()
        
        def GetStackItem(self, item: _TItem, enumerator: IEnumerator[_TItem]) -> _TStackItems:
            return self.__enumerator._GetStackItem(item, enumerator)
        def GetStackItemAsEnumerator(self, item: _TStackItems) -> IEnumerator[_TItem]:
            return self.__enumerator._GetStackItemAsEnumerator(item)
        def GetStackItemAsCookie(self, item: _TStackItems) -> _TCookie:
            return self.__enumerator._GetStackItemAsCookie(item)
        
        def Push(self, item: _TStackItems) -> None:
            if self.__enumerators is None:
                raise InvalidOperationError()
            
            self.__enumerators.Push(item)

        def TryPeek(self) -> INullable[_TStackItems]:
            if self.__enumerators is None:
                raise InvalidOperationError()
            
            return self.__enumerators.TryPeek()

        def TryPop(self) -> INullable[_TStackItems]:
            if self.__enumerators is None:
                raise InvalidOperationError()
            
            self.__enumerators.TryPop()

            return self.__enumerators.TryPeek()
    
        def OnEnteringSublevel(self, item: _TItem) -> bool|None:
            if self.__enumerator._OnEnteringSublevel(item):
                self.__enumerator._OnEnteringLevel(item)

                return True
            
            return False
        def OnExitingSublevel(self, cookie: _TCookie) -> bool|None:
            if self.__enumerator._OnExitingSublevel(cookie):
                self.__enumerator._OnExitingLevel(cookie)

                return True
            
            return False
        
        def OnEnteringMainLevel(self, item: _TItem) -> bool|None:
            if self.__enumerator._OnEnteringMainLevel(item):
                self.__enumerator._OnEnteringLevel(item)

                return True
            
            return False
        def OnExitingMainLevel(self, cookie: _TCookie) -> bool|None:
            if self.__enumerator._OnExitingMainLevel(cookie):
                self.__enumerator._OnExitingLevel(cookie)

                return True
            
            return False
        
        def Dispose(self) -> None:
            if self.__enumerators is not None:
                self.__enumerators.Clear()
                self.__enumerators = None
    
    def __init__(self, enumerator: IEnumerator[TItem], delegate: IRecursiveEnumerationDelegate[TItem]|None, handler: IRecursiveEnumerationHandlerBase[TItem, TCookie]|None) -> None:
        super().__init__(enumerator)
        
        self.__cookie: IRecursiveEnumerationCookie[TItem, TCookie, TStackItems] = RecursiveEnumeratorBase[TItem, TCookie, TStackItems].__Cookie(self, Delegate[TItem](self._GetEnumerator, self._GetEnumerationItems, super()._MoveNextOverride))
        self.__moveNext: IRecursiveEnumerationDelegate[TItem] = NullRecursiveEnumerationDelegate[TItem]() if delegate is None else delegate
        self.__handler: IRecursiveEnumerationHandlerBase[TItem, TCookie] = NullRecursiveEnumerationHandler[TItem, TCookie]() if handler is None else handler
    
    @final
    def _GetCookie(self) -> IRecursiveEnumerationCookie[TItem, TCookie, TStackItems]:
        return self.__cookie
    
    @abstractmethod
    def _GetStackItem(self, item: TItem, enumerator: IEnumerator[TItem]) -> TStackItems:
        pass
    @abstractmethod
    def _GetStackItemAsEnumerator(self, item: TStackItems) -> IEnumerator[TItem]:
        pass
    @abstractmethod
    def _GetStackItemAsCookie(self, item: TStackItems) -> TCookie:
        pass

    def _OnStarting(self) -> bool:
        if super()._OnStarting() and self.__handler.OnStartingEnumeration():
            self.__moveNext.Initialize()

            return True
        
        return False
    
    def _OnEnteringLevel(self, item: TItem) -> None:
        self.__handler.OnEnteringEnumerationLevel(item)
    def _OnExitingLevel(self, cookie: TCookie) -> None:
        self.__handler.OnExitingEnumerationLevel(cookie)
    
    def _OnEnteringSublevel(self, item: TItem) -> bool|None:
        return self.__handler.OnEnteringSubenumerationLevel(item)
    def _OnExitingSublevel(self, cookie: TCookie) -> bool|None:
        return self.__handler.OnExitingSubenumerationLevel(cookie)
    
    def _OnEnteringMainLevel(self, item: TItem) -> bool|None:
        return self.__handler.OnEnteringMainEnumerationLevel(item)
    def _OnExitingMainLevel(self, cookie: TCookie) -> bool|None:
        return self.__handler.OnExitingMainEnumerationLevel(cookie)
    
    @final
    def GetCurrent(self) -> TItem|None:
        return self.__moveNext.GetCurrent()
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNext.MoveNext()
    
    def _OnEnded(self) -> None:
        self.__moveNext.Dispose()

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        self.__handler.OnStoppedEnumeration()