from abc import abstractmethod
from typing import final, Callable

from WinCopies import IInterface
from WinCopies.Collections.Linked.Doubly import DoublyLinkedNode
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
class IWriteOnlyEventManager[TSender, TArgs, TCookie](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, handler: EventHandler[TSender, TArgs]) -> TCookie:
        pass

class IEventManager[TSender, TArgs](IReadOnlyEventManager[TSender, TArgs], IWriteOnlyEventManager[TSender, TArgs, IEvent]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, handler: EventHandler[TSender, TArgs]) -> IEvent:
        pass

class EventManager[TSender, TArgs](IEventManager[TSender, TArgs]):
    class __EventCookie(IEvent):
        def __init__(self, node: DoublyLinkedNode[EventHandler[TSender, TArgs]]):
            super().__init__()

            self.__node: DoublyLinkedNode[EventHandler[TSender, TArgs]] = node
        
        @final
        def Remove(self) -> None:
            self.__node.Remove()
    
    def __init__(self):
        super().__init__()

        self.__events = EnumerableStack[EventHandler[TSender, TArgs]]()
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> IEvent:
        return EventManager.__EventCookie(self.__events._Push(handler))
    
    @final
    def Invoke(self, sender: TSender, args: TArgs) -> bool:
        if self.__events.IsEmpty():
            return False
        
        for event in self.__events:
            event(sender, args)
        
        return True

class ReadOnlyEventManager[TSender, TArgs](IReadOnlyEventManager[TSender, TArgs]):
    def __init__(self, manager: IReadOnlyEventManager[TSender, TArgs]):
        super().__init__()

        self.__manager = manager
    
    @final
    def Invoke(self, sender: TSender, args: TArgs) -> bool:
        return self.__manager.Invoke(sender, args)
class WriteOnlyEventManager[TSender, TArgs](IWriteOnlyEventManager[TSender, TArgs]):
    def __init__(self, manager: IReadOnlyEventManager[TSender, TArgs]):
        super().__init__()
        
        self.__manager = manager
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> None:
        self.__manager.Add(handler)