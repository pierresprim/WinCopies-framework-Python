from __future__ import annotations

from abc import abstractmethod
from typing import cast, final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Iteration import Iterate
from WinCopies.Collections.Iteration.Traversal import EnumerateSafe
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Delegates import NoAction
from WinCopies.Typing.Delegate import Action, Method
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

    @abstractmethod
    def Notify(self, revoke: bool) -> None:
        ...

class _InvalidationNotifierBase(Abstract, IInvalidationNotifier):
    def __init__(self, updater: Method[IInvalidationNotifier]) -> None:
        super().__init__()

        self.__updater: Method[IInvalidationNotifier] = updater

    @final
    def _GetUpdater(self) -> Method[IInvalidationNotifier]:
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

    def __CreateRemovable(self, action: INotifyCallback) -> tuple[_Node, IRemovable]:
        node: _InvalidationNotifier._Removable = object.__new__(_InvalidationNotifier._Removable)
        _node: _Node = _Node(action, lambda: self._OnNodeRemoved(_node, False))

        _InvalidationNotifier._Removable.__init__(node, self, _node)

        return (_node, node)

    @staticmethod
    def Create(action: INotifyCallback, updater: Method[IInvalidationNotifier]) -> IRemovable:
        notifier: _InvalidationNotifier = object.__new__(_InvalidationNotifier)
        _node, node = notifier.__CreateRemovable(action)

        _InvalidationNotifier.__init__(notifier, _node, updater)

        updater(notifier)

        return node
    
    def __init__(self, first: _Node, updater: Method[IInvalidationNotifier]) -> None:
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
                        updater: Method[IInvalidationNotifier] = self._GetUpdater()

                        updater(_DefaultInvalidationNotifier(updater))

                    else: self.__last = previous

                elif node is self.__first: self.__first = cast(_Node, node.GetNext())

            node.Remove(remove)
        
        if safe:
            with self.__monitor: remove()

        else: remove()

    def Add(self, action: INotifyCallback) -> IRemovable:
        with self.__monitor:
            _node, node = self.__CreateRemovable(action)

            self.__last.SetNext(_node)
            self.__last = _node

            return node

        raise

    def Notify(self, revoke: bool) -> None:
        with self.__monitor: EnumerateSafe(Iterate(lambda: self.__first, lambda node: node.GetNext()), lambda node: node.Notify(revoke), True)
@final
class _DefaultInvalidationNotifier(_InvalidationNotifierBase):
    def __init__(self, updater: Method[IInvalidationNotifier]) -> None: super().__init__(updater)

    def Add(self, action: INotifyCallback) -> IRemovable: return _InvalidationNotifier.Create(action, self._GetUpdater())

    def Notify(self, revoke: bool) -> None: pass

class InvalidationNotifier(Abstract, IInvalidationNotifier):
    def __init__(self) -> None:
        def update(notifier: IInvalidationNotifier) -> None: self.__notifier = notifier
        
        super().__init__()

        self.__notifier: IInvalidationNotifier = _DefaultInvalidationNotifier(update) # type: ignore[no-redef]

    @final
    def Add(self, action: INotifyCallback) -> IRemovable: return self.__notifier.Add(action)

    @final
    def Notify(self, revoke: bool) -> None: self.__notifier.Notify(revoke)