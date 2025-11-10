from abc import abstractmethod
from typing import final, Callable

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Linked.Singly import IEnumerableList
from WinCopies.Collections.Linked.Doubly import INode, IList, List
from WinCopies.Collections.Abstraction.Linked import EnumerableStack

type EventHandler[TSender, TArgs] = Callable[[TSender, TArgs], None]

class ICancellableEvent(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Processed(self) -> bool:
        pass

    @abstractmethod
    def Cancel(self) -> None:
        pass

class INotifyableEventBase[T](ICancellableEvent):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> T:
        pass
    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass
class INotifyableEvent(INotifyableEventBase[bool|None]):
    def __init__(self):
        super().__init__()

class ICancellableEventArgs(ICancellableEvent):
    def __init__(self):
        super().__init__()

class INotifyableEventArgsBase[T](ICancellableEventArgs, INotifyableEventBase[T]):
    def __init__(self):
        super().__init__()
class INotifyableEventArgs(INotifyableEventArgsBase[bool|None], INotifyableEvent):
    def __init__(self):
        super().__init__()

class IEvent[T](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetArgs(self) -> T:
        pass
    
    @abstractmethod
    def Remove(self) -> None:
        pass

class IReadOnlyEventManager[TSender, TArgs](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Invoke(self, sender: TSender, args: TArgs) -> bool|None:
        pass
class IWriteOnlyEventManager[TSender, TArgs, TEvent](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, handler: EventHandler[TSender, TArgs]) -> TEvent:
        pass

class IEventManagerBase[TSender, TArgs, TEvent](IReadOnlyEventManager[TSender, TArgs], IWriteOnlyEventManager[TSender, TArgs, TEvent]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, handler: EventHandler[TSender, TArgs]) -> TEvent:
        pass
class IEventManager[TSender, TArgs](IEventManagerBase[TSender, TArgs, IEvent[TSender]]):
    def __init__(self):
        super().__init__()

class CancellableEventArgsBase[T](Abstract, ICancellableEventArgs):
    def __init__(self):
        super().__init__()

        self.__processed: T = self._GetDefaultValue()
    
    @final
    def _GetValue(self) -> T:
        return self.__processed
    @final
    def _SetValue(self, value: T) -> None:
        self.__processed = value
    
    @abstractmethod
    def _GetDefaultValue(self) -> T:
        pass
    @abstractmethod
    def _GetProcessedValue(self) -> T:
        pass
    @abstractmethod
    def _IsProcessed(self, value: T) -> bool:
        pass
    
    @final
    def Processed(self) -> bool:
        return self._IsProcessed(self._GetValue())
    
    @final
    def Cancel(self) -> None:
        self.__processed = self._GetProcessedValue()
class CancellableEventArgs(CancellableEventArgsBase[bool], ICancellableEventArgs):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetDefaultValue(self) -> bool:
        return False
    @final
    def _GetProcessedValue(self) -> bool:
        return True
    @final
    def _IsProcessed(self, value: bool) -> bool:
        return value

class NotifyableEventArgsBase[T](CancellableEventArgsBase[T], INotifyableEventArgsBase[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def GetValue(self) -> T:
        return self._GetValue()
    @final
    def SetValue(self, value: T) -> None:
        self._SetValue(value)
class NotifyableEventArgs(NotifyableEventArgsBase[bool|None], INotifyableEventArgs):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetDefaultValue(self) -> bool|None:
        return False
    @final
    def _GetProcessedValue(self) -> bool|None:
        return None
    @final
    def _IsProcessed(self, value: bool|None) -> bool:
        return value is None

class EventManager[TSender, TArgs](Abstract, IEventManager[TSender, TArgs]):
    class __Event(IEvent[TSender]):
        def __init__(self, node: INode[EventHandler[TSender, TArgs]]):
            super().__init__()

            self.__node: INode[EventHandler[TSender, TArgs]] = node
        
        @final
        def Remove(self) -> None:
            self.__node.Remove()
    
    def __init__(self):
        super().__init__()

        self.__cookies: IList[EventHandler[TSender, TArgs]] = List[EventHandler[TSender, TArgs]]()
        self.__events = EnumerableStack[EventHandler[TSender, TArgs]](self.__cookies)
    
    @final
    def _GetEvents(self) -> IEnumerableList[EventHandler[TSender, TArgs]]:
        return self.__events
    
    def _InvokeEvents(self, sender: TSender, args: TArgs, events: IEnumerableList[EventHandler[TSender, TArgs]]) -> bool:
        for event in events.AsIterable():
            event(sender, args)
        
        return True
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> IEvent[TSender]:
        return EventManager[TSender, TArgs].__Event(self.__cookies.AddLast(handler))
    
    @final
    def Invoke(self, sender: TSender, args: TArgs) -> bool|None:
        events: IEnumerableList[EventHandler[TSender, TArgs]] = self._GetEvents()

        return None if events.IsEmpty() else self._InvokeEvents(sender, args, events)
class CancellableEventManager[TSender, TArgs: ICancellableEvent](EventManager[TSender, TArgs]):
    def __init__(self):
        super().__init__()
    
    def _InvokeEvents(self, sender: TSender, args: TArgs, events: IEnumerableList[EventHandler[TSender, TArgs]]) -> bool:
        for event in events.AsIterable():
            if args.Processed():
                return False
            
            event(sender, args)
        
        return True

class EventManagerAbstractor[TSender, TArgs, TEvent](Abstract):
    def __init__(self, manager: IEventManagerBase[TSender, TArgs, TEvent]):
        super().__init__()

        self.__manager = manager
    
    @final
    def _GetEventManager(self) -> IEventManagerBase[TSender, TArgs, TEvent]:
        return self.__manager

class ReadOnlyEventManager[TSender, TArgs, TEvent](EventManagerAbstractor[TSender, TArgs, TEvent], IReadOnlyEventManager[TSender, TArgs]):
    def __init__(self, manager: IEventManagerBase[TSender, TArgs, TEvent]):
        super().__init__(manager)
    
    @final
    def Invoke(self, sender: TSender, args: TArgs) -> bool|None:
        return self._GetEventManager().Invoke(sender, args)
class WriteOnlyEventManager[TSender, TArgs, TEvent](EventManagerAbstractor[TSender, TArgs, TEvent], IWriteOnlyEventManager[TSender, TArgs, TEvent]):
    def __init__(self, manager: IEventManagerBase[TSender, TArgs, TEvent]):
        super().__init__(manager)
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> TEvent:
        return self._GetEventManager().Add(handler)