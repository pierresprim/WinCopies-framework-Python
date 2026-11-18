from __future__ import annotations

from abc import abstractmethod
from collections import deque
from typing import final, Any
from weakref import ReferenceType, ref

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Iteration import Iterate
from WinCopies.Collections.Iteration.Traversal import Loop
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Delegates import DoNothing, NoAction
from WinCopies.Typing.Delegate import Action, Method, Function, FunctionCall
from WinCopies.Typing.Extensions import IExceptionGroupBuilder, ExceptionGroupBuilder
from WinCopies.Typing.Monitoring import ISafeMonitor, AtomicMonitor, TryDoWork
from WinCopies.Typing.Object import WeakReferenceFinalizer

class INotifyCallback(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Notify(self, revoke: bool) -> None:
        """Notifies this subscriber of an invalidation or a revocation.

        A subscriber leaves the notifier through the IRemovable returned by Add, even during a notification. It is then notified no more, including by the rest of the notification in progress.

        A subscriber can also add a subscriber to the notifier, or notify it again, during a notification. The addition and the new notification wait for the end of the notification in progress, and are then applied in the order in which they were requested. A subscriber added during a notification is therefore not notified by it.

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

            # The notifier unlinks only a node that is neutralized or whose subscriber is gone. This call makes a removed node notify nobody all the same, whoever removes it.
            self.__action.Remove()

            self.__remove = _Remove

            return result
        
        super().__init__()

        self.__action: WeakReferenceFinalizer[INotifyCallback] = WeakReferenceFinalizer[INotifyCallback](action, finalizerProvider)

        self.__remove: FunctionCall[Any] = remove # type: ignore[no-redef]

    def Notify(self, revoke: bool) -> None:
        action: INotifyCallback|None = self.__action.TryGetValue()

        if action is not None: action.Notify(revoke)

    def HasSubscriber(self) -> bool:
        return self.__action.TryGetValue() is not None

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

@final
class _Removable(Abstract, IRemovable):
    def __init__(self, action: Action) -> None:
        def remove() -> None:
            action()

            self.__remove = NoAction

        super().__init__()

        self.__remove: Action = remove # type: ignore[no-redef]

    def Remove(self) -> None: self.__remove()

class IInvalidationNotifier(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Add(self, action: INotifyCallback) -> IRemovable:
        ...

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
    """Notifies its subscribers, which it holds weakly, of an invalidation or a revocation.

    The notifier holds the list of its subscribers, which can be empty, and the transaction that guards it, one monitor, one queue of pending operations, and one request of a purge. An addition, a removal or a notification that finds the monitor free takes it, and is the outermost operation. One that a subscriber requests while the monitor is held waits in the queue, which the outermost operation plays in the order of arrival before it ends. No operation is refused, and none runs in the middle of another.

    The finalizer of a subscriber that dies tries the monitor, which never blocks. If it takes it, it holds it as the outermost operation does, and unlinks the node of the subscriber at once. Otherwise, it requests a purge, which unlinks every node whose subscriber is gone, by a single assignment, and tries the monitor once more, making the purge itself if it takes it. If it does not, the holder of the monitor makes the purge, since the holder reads the request once it has played the queue, and again once it has released the monitor. A finalizer runs at an arbitrary point of the code it interrupts, where no container is guaranteed safe to write, and it queues nothing.

    The exceptions raised by the subscribers during the outermost operation, including in the notifications it plays from the queue, are raised at its end, once everything is applied, alone if there is only one, grouped otherwise. A finalizer that plays the queue raises them at its end, where Python hands them to sys.unraisablehook.
    """

    def __init__(self) -> None:
        super().__init__()

        self.__first: _Node|None = None
        self.__last: _Node|None = None

        self.__monitor: ISafeMonitor = AtomicMonitor()
        self.__queue: deque[Method[Method[Exception]]] = deque()
        self.__mustPurge: bool = False

        self.__notifier: IInvalidationNotifier = _Notifier(self)
        self.__callback: INotifyCallback = _NotifyCallback(self)

    def __Run(self, operation: Method[Method[Exception]]) -> None:
        """Runs an operation with the monitor, which the caller has taken, and then releases the monitor.

        Once the operation is done, even when it raised, the queue is played, including what the queue receives meanwhile, and the list is then purged if a finalizer requested it. The monitor is then released. After the release, the queue and the request are read again, and the drain runs again for as long as either of them calls for it and the monitor is free. A finalizer that found the monitor held made its request before it tried the monitor, so that its purge is not lost.

        Args:
            operation: The operation, which receives the method that collects the exceptions of the subscribers.

        Raises:
            Exception: The exception raised by a subscriber during the operation or the operations played from the queue, or an ExceptionGroup of all of them.
        """
        queue: deque[Method[Method[Exception]]] = self.__queue
        monitor: ISafeMonitor = self.__monitor
        exceptions: IExceptionGroupBuilder|None = None

        def onError(exception: Exception) -> None:
            nonlocal exceptions

            if exceptions is None: exceptions = ExceptionGroupBuilder()

            exceptions.Push(exception)

        def drain() -> None:
            while len(queue) > 0: queue.popleft()(onError)

            if self.__mustPurge:
                # The request is withdrawn before the list is read. A finalizer that runs during the purge makes it again, and that request is read once the monitor is released.
                self.__mustPurge = False

                node: _Node|None = self.__first

                while node is not None:
                    next: _Node|None = node.GetNext()

                    if not node.HasSubscriber(): self.__Unlink(node)

                    node = next

        try:
            try:
                try: operation(onError)
                finally: drain()

            finally: monitor.Dispose()

        finally:
            while (len(queue) > 0 or self.__mustPurge) and TryDoWork(monitor, drain): pass

        if exceptions is not None: exceptions.TryThrow()

    def __Process(self, operation: Method[Method[Exception]]) -> None:
        """Applies an operation to the list, or queues it while another operation holds the monitor.

        An operation that takes the monitor runs at once, and plays the queue and the purge before it ends, as __Run describes. One that finds the monitor held waits in the queue, which the holder plays.

        Args:
            operation: The operation, which receives the method that collects the exceptions of the subscribers.

        Raises:
            Exception: The exception raised by a subscriber during the operation or the operations it played, or an ExceptionGroup of all of them.
        """
        if self.__monitor.TryInitialize(): self.__Run(operation)
        else: self.__queue.append(operation)

    def __Unlink(self, node: _Node) -> None:
        """Unlinks a node from the list, and updates the head and the tail of the list.

        The caller holds the monitor. A node already unlinked is left as it is, since the removal of a node is idempotent.

        Args:
            node: The node.
        """
        def update() -> None:
            if node is self.__last:
                previous: _Node|None = node.GetPrevious()

                if previous is None: self.__first = None

                self.__last = previous

            elif node is self.__first: self.__first = node.GetNext()

        node.Remove(update)

    def __Remove(self, node: _Node) -> None:
        def removeNode(_: Method[Exception]) -> None: self.__Unlink(node)

        node.Neutralize()

        self.__Process(removeNode)

    @final
    def Add(self, action: INotifyCallback) -> IRemovable:
        """Adds a subscriber, held weakly, to this notifier.

        The node of the subscriber and its IRemovable are created at once. During an operation of this notifier, the node is linked once that operation is over, so the subscriber is not notified by a notification in progress.

        Args:
            action: The subscriber.

        Returns:
            The IRemovable through which the subscriber leaves this notifier.

        Raises:
            Exception: The exception raised by a subscriber in a notification that this addition played from the queue, or an ExceptionGroup of all of them.
        """
        def getRemover(notifier: ReferenceType[InvalidationNotifier], node: ReferenceType[_Node]) -> Action:
            def remove() -> None:
                _notifier: InvalidationNotifier|None = notifier()

                if _notifier is not None:
                    _node: _Node|None = node()

                    if _node is not None: _notifier.__Remove(_node)

            return remove

        def setLast(_: Method[Exception]) -> None:
            last: _Node|None = self.__last

            if last is None: self.__first = node
            else: last.SetNext(node)

            self.__last = node

        def requestPurge() -> None:
            # At interpreter exit, the remaining finalizers run while their subscribers are still alive: the node is neutralized first, so that the purge unlinks it all the same. Inside its own finalizer, this touches only the node, since the finalizer has already left its registry.
            node.Neutralize()

            # With no operation in progress, the finalizer takes the monitor, and unlinks its own node without reading the list.
            if self.__monitor.TryInitialize():
                self.__Run(lambda _: self.__Unlink(node))

                return

            # Otherwise, the request is made before the monitor is tried again. If the monitor is still held, its holder reads the request once it has released the monitor, and the purge is not lost; if it was released meanwhile, the second try takes it.
            self.__mustPurge = True

            if self.__monitor.TryInitialize(): self.__Run(DoNothing)

        node: _Node = _Node(action, requestPurge)
        removable: IRemovable = _Removable(getRemover(ref(self), ref(node)))

        self.__Process(setLast)

        return removable

    @final
    def Notify(self, revoke: bool) -> None:
        """Notifies the subscribers of this notifier, in the order in which they were added.

        During an operation of this notifier, the notification waits for the end of that operation, and then reaches the subscribers as they are at that time.

        Args:
            revoke: True for a revocation, False for an invalidation.

        Raises:
            Exception: The exception raised by a subscriber, or an ExceptionGroup of all of them, once every subscriber is notified and the queue is played.
        """
        # With the monitor free and the queue empty, no operation is in progress, and an empty list has nobody to notify, nor to purge. The notification then returns without allocating anything.
        if not self.__monitor.IsBusy() and len(self.__queue) == 0 and self.__first is None: return

        def notify(onError: Method[Exception]) -> None:
            def process(node: _Node) -> None:
                try: node.Notify(revoke)
                except Exception as e: onError(e)

            Loop(Iterate(lambda: self.__first, lambda node: node.GetNext()), process)

        self.__Process(notify)

    @final
    def AsCallback(self) -> INotifyCallback: return self.__callback
    @final
    def AsNotifier(self) -> IInvalidationNotifier: return self.__notifier