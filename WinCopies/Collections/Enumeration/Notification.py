from __future__ import annotations

from abc import abstractmethod
from collections import deque
from typing import cast, final, Any
from weakref import ReferenceType, ref

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Iteration import Iterate
from WinCopies.Collections.Iteration.Traversal import EnumerateSafe
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Delegates import NoAction
from WinCopies.Typing.Delegate import Action, Method, Function, FunctionCall
from WinCopies.Typing.Monitoring import IMonitor, Monitor, TryDoWork
from WinCopies.Typing.Object import WeakReferenceFinalizer

class INotifyCallback(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Notify(self, revoke: bool) -> None:
        """Notifies this subscriber of an invalidation or a revocation.

        A subscriber leaves the notifier through the IRemovable returned by Add, even during a notification. It is then notified no more, including by the rest of the notification in progress.

        Args:
            revoke: True for a revocation, False for an invalidation.
        """
        ...

def _Remove(action: Function[Any]) -> Any:
    return None

@final
class _Node(Abstract):
    def __init__(self, action: INotifyCallback, finalizerProvider: Function[Any]) -> None:
        self.__previous: _Node|None = None
        self.__next: _Node|None = None

        def remove(action: Function[Any]) -> Any:
            def unlink() -> None:
                previous: _Node|None = self.__previous
                next: _Node|None = self.GetNext()
        
                if next is None:
                    if previous is not None:
                        previous.__next = None
                        self.__previous = None
        
                    return
                
                if previous is not None:
                    previous.SetNext(next)
                    self.__previous = None
                
                next.__previous = previous
            
            result: Any = action()

            unlink()

            # At interpreter exit, the remaining finalizers run while their subscribers are still alive, and this call is then what neutralizes the node.
            self.__action.Remove()

            self.__remove = _Remove

            return result
        
        super().__init__()

        self.__action: WeakReferenceFinalizer[INotifyCallback] = WeakReferenceFinalizer[INotifyCallback](action, finalizerProvider)

        self.__remove: FunctionCall[Any] = remove # type: ignore[no-redef]

    def Notify(self, revoke: bool) -> None:
        action: INotifyCallback|None = self.__action.TryGetValue()

        if action is not None: action.Notify(revoke)

    def GetPrevious(self) -> _Node|None:
        return self.__previous

    def GetNext(self) -> _Node|None:
        return self.__next
    def SetNext(self, node: _Node) -> None:
        self.__next = node
        node.__previous = self

    def Neutralize(self) -> None:
        self.__action.Remove()

    def Remove[T](self, action: Function[T]) -> T:
        remove: FunctionCall[T] = self.__remove

        return remove(action)

class IInvalidationNotifier(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Add(self, action: INotifyCallback) -> IRemovable:
        ...
class _IInvalidationNotifier(INotifyCallback, IInvalidationNotifier):
    def __init__(self) -> None: super().__init__()

class _InvalidationNotifierBase(Abstract, _IInvalidationNotifier):
    def __init__(self, updater: Method[_IInvalidationNotifier]) -> None:
        super().__init__()

        self.__updater: Method[_IInvalidationNotifier] = updater

    @final
    def _GetUpdater(self) -> Method[_IInvalidationNotifier]:
        return self.__updater

@final
class _InvalidationNotifier(_InvalidationNotifierBase):
    @final
    class _Removable(Abstract, IRemovable):
        def __init__(self, notifier: ReferenceType[_InvalidationNotifier], node: _Node) -> None:
            def getRemovable(node: ReferenceType[_Node]) -> Action:
                def remove() -> None:
                    _notifier: _InvalidationNotifier|None = notifier()

                    if _notifier is not None:
                        _node: _Node|None = node()

                        if _node is not None: _notifier._OnNodeRemoved(_node, True)
                    
                    self.__remove = NoAction

                return remove

            super().__init__()

            self.__remove: Action = getRemovable(ref(node)) # type: ignore[no-redef]

        def Remove(self) -> None: self.__remove()

    @staticmethod
    def __CreateNode(action: INotifyCallback, notifier: Function[_InvalidationNotifier]) -> _Node:
        node: _Node = _Node(action, lambda: notifier()._OnNodeRemoved(node, False))

        return node

    def __CreateRemovable(self, node: _Node) -> IRemovable:
        return _InvalidationNotifier._Removable(ref(self), node)

    @staticmethod
    def Create(action: INotifyCallback, updater: Method[_IInvalidationNotifier]) -> IRemovable:
        notifier: _InvalidationNotifier
        node: _Node = _InvalidationNotifier.__CreateNode(action, lambda: notifier)

        updater(notifier := _InvalidationNotifier(node, updater))

        return notifier.__CreateRemovable(node)
    
    def __init__(self, first: _Node, updater: Method[_IInvalidationNotifier]) -> None:
        super().__init__(updater)

        self.__first: _Node = first
        self.__last: _Node = first

        self.__monitor: IMonitor = Monitor()
        self.__removals: deque[_Node] = deque()
        self.__isRetired: bool = False

    def __Update(self) -> None:
        updater: Method[_IInvalidationNotifier] = self._GetUpdater()

        self.__isRetired = True
        
        updater(_DefaultInvalidationNotifier(updater))

    def __Drain(self) -> None:
        def remove(node: _Node) -> None:
            def remove() -> None:
                if node is self.__last:
                    previous: _Node|None = node.GetPrevious()

                    if previous is None: self.__Update()
                    else: self.__last = previous

                elif node is self.__first: self.__first = cast(_Node, node.GetNext())

            node.Remove(remove)

        while self.__removals: remove(self.__removals.pop())

    def __Commit(self) -> None:
        while len(self.__removals) > 0 and TryDoWork(self.__monitor, self.__Drain): pass

    def __Process[T](self, func: Function[T]) -> T:
        try:
            with self.__monitor:
                try: return func()
                finally: self.__Drain()

        finally: self.__Commit()

        raise

    def _OnNodeRemoved(self, node: _Node, explicit: bool) -> None:
        if explicit: node.Neutralize()

        self.__removals.append(node)

        self.__Commit()

    def Add(self, action: INotifyCallback) -> IRemovable:
        def add() -> IRemovable:
            if self.__isRetired: return _InvalidationNotifier.Create(action, self._GetUpdater())

            node: _Node = _InvalidationNotifier.__CreateNode(action, lambda: self)

            self.__last.SetNext(node)
            self.__last = node

            return self.__CreateRemovable(node)

        return self.__Process(add)

    def Notify(self, revoke: bool) -> None:
        self.__Process(lambda: EnumerateSafe(Iterate(lambda: self.__first, lambda node: node.GetNext()), lambda node: node.Notify(revoke), True))
@final
class _DefaultInvalidationNotifier(_InvalidationNotifierBase):
    def __init__(self, updater: Method[_IInvalidationNotifier]) -> None: super().__init__(updater)

    def Add(self, action: INotifyCallback) -> IRemovable: return _InvalidationNotifier.Create(action, self._GetUpdater())

    def Notify(self, revoke: bool) -> None: pass

@final
class _NotifyCallback(Abstract, INotifyCallback):
    def __init__(self, callback: INotifyCallback) -> None:
        super().__init__()

        self.__callback: INotifyCallback = callback

    def Notify(self, revoke: bool) -> None: self.__callback.Notify(revoke)
@final
class _Notifier(Abstract, IInvalidationNotifier):
    def __init__(self, notifier: IInvalidationNotifier) -> None:
        super().__init__()

        self.__notifier: IInvalidationNotifier = notifier

    def Add(self, action: INotifyCallback) -> IRemovable: return self.__notifier.Add(action)

class IInvalidationNotifierProvider(INotifyCallback, IInvalidationNotifier):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsCallback(self) -> INotifyCallback:
        ...
    @abstractmethod
    def AsNotifier(self) -> IInvalidationNotifier:
        ...
class InvalidationNotifier(Abstract, IInvalidationNotifierProvider):
    def __init__(self) -> None:
        def update(notifier: _IInvalidationNotifier) -> None: self.__notifierProvider = notifier
        
        super().__init__()

        self.__notifierProvider: _IInvalidationNotifier = _DefaultInvalidationNotifier(update) # type: ignore[no-redef]

        self.__notifier: IInvalidationNotifier = _Notifier(self)
        self.__callback: INotifyCallback = _NotifyCallback(self)

    @final
    def Add(self, action: INotifyCallback) -> IRemovable: return self.__notifierProvider.Add(action)

    @final
    def Notify(self, revoke: bool) -> None: self.__notifierProvider.Notify(revoke)

    @final
    def AsCallback(self) -> INotifyCallback: return self.__callback
    @final
    def AsNotifier(self) -> IInvalidationNotifier: return self.__notifier