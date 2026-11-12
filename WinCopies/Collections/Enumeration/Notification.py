from __future__ import annotations

from abc import abstractmethod
from typing import cast, final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Iteration import Iterate
from WinCopies.Collections.Iteration.Traversal import EnumerateSafe
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Delegates import NoAction
from WinCopies.Typing.Delegate import Action, Method, Function
from WinCopies.Typing.Monitoring import IMonitor, Monitor
from WinCopies.Typing.Object import WeakReferenceFinalizer

class INotifyCallback(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Notify(self, revoke: bool) -> None:
        ...

@final
class _Node(Abstract):
    def __init__(self, action: INotifyCallback, finalizerProvider: Action) -> None:
        self.__previous: _Node|None = None
        self.__next: _Node|None = None

        def remove(action: Action) -> None:
            def remove() -> None:
                previous: _Node|None = self.__previous
                next: _Node|None = self.GetNext()
        
                self.__action.Remove()
        
                if next is None:
                    if previous is not None:
                        previous.__next = None
                        self.__previous = None
        
                    return
                
                if previous is not None:
                    previous.SetNext(next)
                    self.__previous = None
                
                next.__previous = previous
                self.__next = None

            action()

            remove()

            self.__remove = lambda _: None
        
        super().__init__()

        self.__action: WeakReferenceFinalizer[INotifyCallback] = WeakReferenceFinalizer[INotifyCallback](action, finalizerProvider)

        self.__remove: Method[Action] = remove # type: ignore[no-redef]

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

    def Remove(self, action: Action) -> None:
        remove: Method[Action] = self.__remove

        remove(action)

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
        def __init__(self, notifier: _InvalidationNotifier, node: _Node) -> None:
            def remove() -> None:
                notifier._OnNodeRemoved(node, True)
                
                self.__remove = NoAction

            super().__init__()

            self.__remove: Action = remove # type: ignore[no-redef]

        def Remove(self) -> None: self.__remove()

    @staticmethod
    def __CreateNode(action: INotifyCallback, notifier: Function[_InvalidationNotifier]) -> _Node:
        node: _Node = _Node(action, lambda: notifier()._OnNodeRemoved(node, False))

        return node

    @staticmethod
    def Create(action: INotifyCallback, updater: Method[_IInvalidationNotifier]) -> IRemovable:
        notifier: _InvalidationNotifier
        node: _Node = _InvalidationNotifier.__CreateNode(action, lambda: notifier)

        notifier = _InvalidationNotifier(node, updater)

        updater(notifier)

        return _InvalidationNotifier._Removable(notifier, node)
    
    def __init__(self, first: _Node, updater: Method[_IInvalidationNotifier]) -> None:
        super().__init__(updater)

        self.__first: _Node = first
        self.__last: _Node = first

        self.__monitor: IMonitor = Monitor()

    def _OnNodeRemoved(self, node: _Node, safe: bool) -> None:
        def remove() -> None:
            def remove() -> None:
                if node is self.__last:
                    previous: _Node|None = node.GetPrevious()

                    if previous is None:
                        updater: Method[_IInvalidationNotifier] = self._GetUpdater()

                        updater(_DefaultInvalidationNotifier(updater))

                    else: self.__last = previous

                elif node is self.__first: self.__first = cast(_Node, node.GetNext())

            node.Remove(remove)
        
        if safe:
            with self.__monitor: remove()

        else: remove()

    def Add(self, action: INotifyCallback) -> IRemovable:
        with self.__monitor:
            node: _Node = _InvalidationNotifier.__CreateNode(action, lambda: self)

            self.__last.SetNext(node)
            self.__last = node

            return _InvalidationNotifier._Removable(self, node)

        raise

    def Notify(self, revoke: bool) -> None:
        with self.__monitor: EnumerateSafe(Iterate(lambda: self.__first, lambda node: node.GetNext()), lambda node: node.Notify(revoke), True)
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

    def Notify(self, revoke: bool) -> None: return self.__callback.Notify(revoke)
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