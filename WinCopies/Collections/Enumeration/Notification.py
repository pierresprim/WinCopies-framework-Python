from __future__ import annotations

from abc import abstractmethod
from typing import cast, final, Any, Literal
from weakref import ReferenceType, ref

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Iteration import Iterate
from WinCopies.Collections.Iteration.Traversal import EnumerateSafe
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Delegates import NoAction, DoNothing
from WinCopies.Typing.Delegate import Action, Method, Function, FunctionCall
from WinCopies.Typing.Monitoring import IMonitor, Monitor
from WinCopies.Typing.Object import WeakReferenceFinalizer

class INotifyCallback(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Notify(self, revoke: bool) -> bool|None:
        """Notifies this subscriber of an invalidation or a revocation.

        Args:
            revoke: True for a revocation, False for an invalidation.

        Returns:
            - True to leave the notifier: the subscriber is removed once this call has returned, and is notified no more. This is the only way to leave from within a notification, during which the IRemovable returned by Add cannot be used.
            - False to stay.
            - None to stay as well, for a notifier subscribed to another one: at least one of its own subscribers left during this notification by returning True. The notifier it is subscribed to takes it as a False. A subscriber that dies during the notification has not left: it has ceased to exist, which is not reported.
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

            self.__action.Remove()

            self.__remove = _Remove

            return result
        
        super().__init__()

        self.__action: WeakReferenceFinalizer[INotifyCallback] = WeakReferenceFinalizer[INotifyCallback](action, finalizerProvider)

        self.__remove: FunctionCall[Any] = remove # type: ignore[no-redef]

    def Notify(self, revoke: bool) -> bool:
        action: INotifyCallback|None = self.__action.TryGetValue()

        return action is not None and action.Notify(revoke) is True

    def GetPrevious(self) -> _Node|None:
        return self.__previous

    def GetNext(self) -> _Node|None:
        return self.__next
    def SetNext(self, node: _Node) -> None:
        self.__next = node
        node.__previous = self

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
        def __init__(self, notifier: _InvalidationNotifier, node: _Node) -> None:
            def getRemovable(node: ReferenceType[_Node]) -> Action:
                def remove() -> None:
                    _node: _Node|None = node()

                    if _node is not None: notifier._OnNodeRemoved(_node, True)
                    
                    self.__remove = NoAction

                return remove

            super().__init__()

            self.__remove: Action = getRemovable(ref(node)) # type: ignore[no-redef]

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

    def __Update(self) -> None:
        updater: Method[_IInvalidationNotifier] = self._GetUpdater()
        
        updater(_DefaultInvalidationNotifier(updater))

    def _OnNodeRemoved(self, node: _Node, safe: bool|None) -> bool:
        def remove(update: bool) -> bool:
            def remove() -> bool:
                if node is self.__last:
                    previous: _Node|None = node.GetPrevious()

                    if previous is None:
                        if update:
                            self.__Update()

                        else: return True

                    else: self.__last = previous

                elif node is self.__first: self.__first = cast(_Node, node.GetNext())

                return False

            return node.Remove(remove)
        
        if safe is True:
            with self.__monitor: remove(True)

            return False

        return remove(safe is False)

    def Add(self, action: INotifyCallback) -> IRemovable:
        with self.__monitor:
            node: _Node = _InvalidationNotifier.__CreateNode(action, lambda: self)

            self.__last.SetNext(node)
            self.__last = node

            return _InvalidationNotifier._Removable(self, node)

        raise

    def Notify(self, revoke: bool) -> Literal[False]|None:
        action: Method[_Node] = DoNothing
        update: Action = NoAction

        def notify(node: _Node) -> None:
            nonlocal action

            def __notify(node: _Node) -> bool:
                return node.Notify(revoke)

            def _notify(node: _Node) -> None:
                nonlocal update

                if self._OnNodeRemoved(node, None): update = self.__Update

            def notify(node: _Node) -> None:
                if __notify(node): _notify(node)

            if __notify(node):
                _notify(node)

                action = notify

        with self.__monitor:
            action = notify

            try: EnumerateSafe(Iterate(lambda: self.__first, lambda node: node.GetNext()), lambda node: action(node), True)
            finally: update()

        return False if action == notify else None
@final
class _DefaultInvalidationNotifier(_InvalidationNotifierBase):
    def __init__(self, updater: Method[_IInvalidationNotifier]) -> None: super().__init__(updater)

    def Add(self, action: INotifyCallback) -> IRemovable: return _InvalidationNotifier.Create(action, self._GetUpdater())

    def Notify(self, revoke: bool) -> bool: return False

@final
class _NotifyCallback(Abstract, INotifyCallback):
    def __init__(self, callback: INotifyCallback) -> None:
        super().__init__()

        self.__callback: INotifyCallback = callback

    def Notify(self, revoke: bool) -> bool|None: return self.__callback.Notify(revoke)
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
    def Notify(self, revoke: bool) -> bool|None: return self.__notifierProvider.Notify(revoke)

    @final
    def AsCallback(self) -> INotifyCallback: return self.__callback
    @final
    def AsNotifier(self) -> IInvalidationNotifier: return self.__notifier