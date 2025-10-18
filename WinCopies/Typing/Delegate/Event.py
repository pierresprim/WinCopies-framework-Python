from abc import abstractmethod
from typing import final, Callable

from WinCopies import IInterface
from WinCopies.Collections.Linked.Singly import IEnumerable
from WinCopies.Collections.Linked.Doubly import INode, IList, List
from WinCopies.Collections.Abstraction.Linked import EnumerableStack

type EventHandler[TSender, TArgs] = Callable[[TSender, TArgs], None]

class IEvent(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Remove(self) -> None:
        pass

class IReadOnlyEventManager[TSender, TArgs](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Invoke(self, sender: TSender, args: TArgs) -> bool:
        pass
class IWriteOnlyEventManager[TSender, TArgs, TEvent: IEvent](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, handler: EventHandler[TSender, TArgs]) -> TEvent:
        pass

class IEventManagerBase[TSender, TArgs, TEvent: IEvent](IReadOnlyEventManager[TSender, TArgs], IWriteOnlyEventManager[TSender, TArgs, TEvent]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, handler: EventHandler[TSender, TArgs]) -> TEvent:
        pass
class IEventManager[TSender, TArgs](IEventManagerBase[TSender, TArgs, IEvent]):
    def __init__(self):
        super().__init__()

class EventManager[TSender, TArgs](IEventManager[TSender, TArgs]):
    class __Event(IEvent):
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
    def _GetEvents(self) -> IEnumerable[EventHandler[TSender, TArgs]]:
        return self.__events
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> IEvent:
        return EventManager.__Event(self.__cookies.AddLast(handler))
    
    @final
    def Invoke(self, sender: TSender, args: TArgs) -> bool:
        if self.__events.IsEmpty():
            return False
        
        for event in self.__events.AsIterable():
            event(sender, args)
        
        return True

class EventManagerAbstractor[TSender, TArgs, TEvent: IEvent](IInterface):
    def __init__(self, manager: IEventManagerBase[TSender, TArgs, TEvent]):
        super().__init__()

        self.__manager = manager
    
    @final
    def _GetEventManager(self) -> IEventManagerBase[TSender, TArgs, TEvent]:
        return self.__manager

class ReadOnlyEventManager[TSender, TArgs, TEvent: IEvent](EventManagerAbstractor[TSender, TArgs, TEvent], IReadOnlyEventManager[TSender, TArgs]):
    def __init__(self, manager: IEventManagerBase[TSender, TArgs, TEvent]):
        super().__init__(manager)
    
    @final
    def Invoke(self, sender: TSender, args: TArgs) -> bool:
        return self._GetEventManager().Invoke(sender, args)
class WriteOnlyEventManager[TSender, TArgs, TEvent: IEvent](EventManagerAbstractor[TSender, TArgs, TEvent], IWriteOnlyEventManager[TSender, TArgs, TEvent]):
    def __init__(self, manager: IEventManagerBase[TSender, TArgs, TEvent]):
        super().__init__(manager)
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> TEvent:
        return self._GetEventManager().Add(handler)