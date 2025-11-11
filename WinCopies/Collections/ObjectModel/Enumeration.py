from abc import abstractmethod
from typing import final

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Collections.Enumeration.Recursive import IRecursiveEnumerationHandlerBase, IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler

from WinCopies.Typing import InvalidOperationError, IMonitor, Monitor
from WinCopies.Typing.Delegate.Event import IEvent, INotifyableEvent, IEventManager, CancellableEventArgs, NotifyableEventArgs, EventHandler, EventManager, CancellableEventManager
from WinCopies.Typing.Pairing import DualValueNullableBool

class ILevelChangedEventArgs[T](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetItem(self) -> T:
        pass

class LevelChangedEventArgs[T](Abstract, ILevelChangedEventArgs[T]):
    def __init__(self, item: T):
        super().__init__()

        self.__item: T = item
    
    @final
    def GetItem(self) -> T:
        return self.__item
class NotifyableLevelChangedEventArgs[T](NotifyableEventArgs, ILevelChangedEventArgs[T]):
    def __init__(self, item: T):
        super().__init__()

        self.__item: T = item
    
    @final
    def GetItem(self) -> T:
        return self.__item

class EnteringLevelEventArgs[T](LevelChangedEventArgs[T]):
    def __init__(self, item: T):
        super().__init__(item)
class NotifyableEnteringLevelEventArgs[T](NotifyableLevelChangedEventArgs[T]):
    def __init__(self, item: T):
        super().__init__(item)

class _IEventManagerAbstract[TSender, TArgs](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Invoke(self, sender: TSender, args: TArgs) -> bool|None:
        pass
class _EventManagerAbstract[TSender, TArgs](Abstract, _IEventManagerAbstract[TSender, TArgs]):
    def __init__(self):
        super().__init__()
        
        self.__eventManager: IEventManager[TSender, TArgs] = self._GetEventManager()
    
    @abstractmethod
    def _GetEventManager(self) -> IEventManager[TSender, TArgs]:
        pass
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> IEvent[TSender]:
        return self.__eventManager.Add(handler)
    
    @final
    def Invoke(self, sender: TSender, args: TArgs) -> bool|None:
        return self.__eventManager.Invoke(sender, args)

class _EventManagerBase[TSender, TArgs](_EventManagerAbstract[TSender, TArgs]):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetEventManager(self) -> IEventManager[TSender, TArgs]:
        return EventManager[TSender, TArgs]()
class _NotifyableEventManagerBase[TSender, TArgs: INotifyableEvent](_EventManagerAbstract[TSender, TArgs]):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetEventManager(self) -> IEventManager[TSender, TArgs]:
        return CancellableEventManager[TSender, TArgs]()

class _StartingEventManager[T](_EventManagerBase[T, CancellableEventArgs]):
    def __init__(self):
        super().__init__()
    
    @final
    def InvokeWithDefaultArgs(self, sender: T) -> bool|None:
        return self.Invoke(sender, CancellableEventArgs())
class _EventManager[T](_EventManagerBase[T, None]):
    def __init__(self):
        super().__init__()
    
    @final
    def InvokeEvents(self, sender: T) -> bool|None:
        return self.Invoke(sender, None)

class _ILevelEventManagerAbstract[TSender, TCookie, TArgs](_IEventManagerAbstract[TSender, TArgs]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetEventArgs(self, item: TCookie) -> TArgs:
        pass

    @final
    def InvokeFromCookie(self, sender: TSender, item: TCookie) -> DualValueNullableBool[TArgs]:
        args: TArgs = self._GetEventArgs(item)

        return DualValueNullableBool[TArgs](args, self.Invoke(sender, args))

class _LevelEventManagerBase[TSender, TCookie, TArgs](_EventManagerBase[TSender, TArgs], _ILevelEventManagerAbstract[TSender, TCookie, TArgs]):
    def __init__(self):
        super().__init__()
class _NotifyableLevelEventManagerBase[TSender, TCookie, TArgs: INotifyableEvent](_NotifyableEventManagerBase[TSender, TArgs], _ILevelEventManagerAbstract[TSender, TCookie, TArgs]):
    def __init__(self):
        super().__init__()

@final
class _LevelEventManager[TSender, TCookie](_LevelEventManagerBase[TSender, TCookie, LevelChangedEventArgs[TCookie]]):
    def __init__(self):
        super().__init__()
    
    def _GetEventArgs(self, item: TCookie) -> LevelChangedEventArgs[TCookie]:
        return LevelChangedEventArgs[TCookie](item)
@final
class _EnteringLevelEventManager[TSender, TItem](_LevelEventManagerBase[TSender, TItem, EnteringLevelEventArgs[TItem]]):
    def __init__(self):
        super().__init__()
    
    def _GetEventArgs(self, item: TItem) -> EnteringLevelEventArgs[TItem]:
        return EnteringLevelEventArgs[TItem](item)

@final
class _NotifyableLevelEventManager[TSender, TCookie](_NotifyableLevelEventManagerBase[TSender, TCookie, NotifyableLevelChangedEventArgs[TCookie]]):
    def __init__(self):
        super().__init__()
    
    def _GetEventArgs(self, item: TCookie) -> NotifyableLevelChangedEventArgs[TCookie]:
        return NotifyableLevelChangedEventArgs[TCookie](item)
@final
class _NotifyableEnteringLevelEventManager[TSender, TItem](_NotifyableLevelEventManagerBase[TSender, TItem, NotifyableEnteringLevelEventArgs[TItem]]):
    def __init__(self):
        super().__init__()
    
    def _GetEventArgs(self, item: TItem) -> NotifyableEnteringLevelEventArgs[TItem]:
        return NotifyableEnteringLevelEventArgs[TItem](item)

class IDelegateRecursiveEnumerationHandlerBase[TSender, TItem, TCookie](IRecursiveEnumerationHandlerBase[TItem, TCookie]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def OnStarting(self, handler: EventHandler[TSender, CancellableEventArgs]) -> IEvent[TSender]:
        pass
    @abstractmethod
    def OnStopped(self, handler: EventHandler[TSender, None]) -> IEvent[TSender]:
        pass
    
    @abstractmethod
    def OnEnteringLevel(self, handler: EventHandler[TSender, EnteringLevelEventArgs[TItem]]) -> IEvent[TSender]:
        pass
    @abstractmethod
    def OnExitingLevel(self, handler: EventHandler[TSender, LevelChangedEventArgs[TCookie]]) -> IEvent[TSender]:
        pass
    
    @abstractmethod
    def OnEnteringMainLevel(self, handler: EventHandler[TSender, NotifyableEnteringLevelEventArgs[TItem]]) -> IEvent[TSender]:
        pass
    @abstractmethod
    def OnExitingMainLevel(self, handler: EventHandler[TSender, NotifyableLevelChangedEventArgs[TCookie]]) -> IEvent[TSender]:
        pass
    
    @abstractmethod
    def OnEnteringSublevel(self, handler: EventHandler[TSender, NotifyableEnteringLevelEventArgs[TItem]]) -> IEvent[TSender]:
        pass
    @abstractmethod
    def OnExitingSublevel(self, handler: EventHandler[TSender, NotifyableLevelChangedEventArgs[TCookie]]) -> IEvent[TSender]:
        pass
class IDelegateRecursiveEnumerationHandler[TSender, TItem](IDelegateRecursiveEnumerationHandlerBase[TSender, TItem, None], IRecursiveEnumerationHandler[TItem]):
    def __init__(self):
        super().__init__()
class IDelegateRecursiveStackedEnumerationHandler[TSender, TItem](IDelegateRecursiveEnumerationHandlerBase[TSender, TItem, TItem], IRecursiveStackedEnumerationHandler[TItem]):
    def __init__(self):
        super().__init__()

class RecursiveEnumerationHandlerBase[TSender, TItem, TCookie](Abstract, IDelegateRecursiveEnumerationHandlerBase[TSender, TItem, TCookie]):
    def __init__(self, sender: TSender):
        def getEntranceLevelEventManager() -> _NotifyableEnteringLevelEventManager[TSender, TItem]:
            return _NotifyableEnteringLevelEventManager[TSender, TItem]()
        def getExitLevelEventManager() -> _NotifyableLevelEventManager[TSender, TCookie]:
            return _NotifyableLevelEventManager[TSender, TCookie]()
        
        super().__init__()

        self.__starting: _StartingEventManager[TSender] = _StartingEventManager[TSender]()
        self.__stopped: _EventManager[TSender] = _EventManager[TSender]()

        self.__enteringLevel: _EnteringLevelEventManager[TSender, TItem] = _EnteringLevelEventManager[TSender, TItem]()
        self.__exitingLevel: _LevelEventManager[TSender, TCookie] = _LevelEventManager[TSender, TCookie]()

        self.__enteringMainLevel: _NotifyableEnteringLevelEventManager[TSender, TItem] = getEntranceLevelEventManager()
        self.__exitingMainLevel: _NotifyableLevelEventManager[TSender, TCookie] = getExitLevelEventManager()

        self.__enteringSublevel: _NotifyableEnteringLevelEventManager[TSender, TItem] = getEntranceLevelEventManager()
        self.__exitingSublevel: _NotifyableLevelEventManager[TSender, TCookie] = getExitLevelEventManager()
        
        self.__monitor: IMonitor = Monitor()

        self.__sender: TSender = sender
    
    @final
    def __AssertReentrancy(self) -> None:
        if self.__monitor.IsBusy():
            raise InvalidOperationError("No reentrancy allowed.")
    @final
    def __BlockReentrancy(self) -> IDisposable:
        self.__monitor.Initialize()

        return self.__monitor
    
    @final
    def __OnEvent[TArgs](self, eventManager: _EventManagerAbstract[TSender, TArgs], handler: EventHandler[TSender, TArgs]) -> IEvent[TSender]:
        with self.__BlockReentrancy():
            return eventManager.Add(handler)
        
        raise

    @final
    def __InvokeEvent[TArgsCookie, TArgs](self, item: TArgsCookie, eventManager: _ILevelEventManagerAbstract[TSender, TArgsCookie, TArgs]) -> DualValueNullableBool[TArgs]:
        self.__AssertReentrancy()
        
        return eventManager.InvokeFromCookie(self._GetSender(), item)
    @final
    def __InvokeNotifyableEvent[TArgsCookie, TArgs: INotifyableEvent](self, item: TArgsCookie, eventManager: _NotifyableLevelEventManagerBase[TSender, TArgsCookie, TArgs]) -> bool|None:
        return self.__InvokeEvent(item, eventManager).GetKey().GetValue()
    
    @final
    def _GetSender(self) -> TSender:
        return self.__sender
    
    @final
    def OnStarting(self, handler: EventHandler[TSender, CancellableEventArgs]) -> IEvent[TSender]:
        return self.__OnEvent(self.__starting, handler)
    @final
    def OnStopped(self, handler: EventHandler[TSender, None]) -> IEvent[TSender]:
        return self.__OnEvent(self.__stopped, handler)
    
    @final
    def OnEnteringLevel(self, handler: EventHandler[TSender, EnteringLevelEventArgs[TItem]]) -> IEvent[TSender]:
        return self.__OnEvent(self.__enteringLevel, handler)
    @final
    def OnExitingLevel(self, handler: EventHandler[TSender, LevelChangedEventArgs[TCookie]]) -> IEvent[TSender]:
        return self.__OnEvent(self.__exitingLevel, handler)
    
    @final
    def OnEnteringMainLevel(self, handler: EventHandler[TSender, NotifyableEnteringLevelEventArgs[TItem]]) -> IEvent[TSender]:
        return self.__OnEvent(self.__enteringMainLevel, handler)
    @final
    def OnExitingMainLevel(self, handler: EventHandler[TSender, NotifyableLevelChangedEventArgs[TCookie]]) -> IEvent[TSender]:
        return self.__OnEvent(self.__exitingMainLevel, handler)
    
    @final
    def OnEnteringSublevel(self, handler: EventHandler[TSender, NotifyableEnteringLevelEventArgs[TItem]]) -> IEvent[TSender]:
        return self.__OnEvent(self.__enteringSublevel, handler)
    @final
    def OnExitingSublevel(self, handler: EventHandler[TSender, NotifyableLevelChangedEventArgs[TCookie]]) -> IEvent[TSender]:
        return self.__OnEvent(self.__exitingSublevel, handler)

    def OnStartingEnumeration(self) -> bool:
        self.__AssertReentrancy()

        return self.__starting.InvokeWithDefaultArgs(self._GetSender()) is not False
    
    def OnEnteringEnumerationLevel(self, item: TItem) -> None:
        self.__InvokeEvent(item, self.__enteringLevel)
    def OnExitingEnumerationLevel(self, cookie: TCookie) -> None:
        self.__InvokeEvent(cookie, self.__exitingLevel)
    
    def OnEnteringMainEnumerationLevel(self, item: TItem) -> bool|None:
        return self.__InvokeNotifyableEvent(item, self.__enteringMainLevel)
    def OnExitingMainEnumerationLevel(self, cookie: TCookie) -> bool|None:
        return self.__InvokeNotifyableEvent(cookie, self.__exitingMainLevel)
    
    def OnEnteringSubenumerationLevel(self, item: TItem) -> bool|None:
        return self.__InvokeNotifyableEvent(item, self.__enteringSublevel)
    def OnExitingSubenumerationLevel(self, cookie: TCookie) -> bool|None:
        return self.__InvokeNotifyableEvent(cookie, self.__exitingSublevel)
    
    def OnStoppedEnumeration(self) -> None:
        self.__AssertReentrancy()
        
        self.__stopped.InvokeEvents(self._GetSender())

class RecursiveEnumerationHandler[TSender, TItem](RecursiveEnumerationHandlerBase[TSender, TItem, None], IDelegateRecursiveEnumerationHandler[TSender, TItem]):
    def __init__(self, sender: TSender):
        super().__init__(sender)
class RecursiveStackedEnumerationHandler[TSender, TItem](RecursiveEnumerationHandlerBase[TSender, TItem, TItem], IDelegateRecursiveStackedEnumerationHandler[TSender, TItem]):
    def __init__(self, sender: TSender):
        super().__init__(sender)