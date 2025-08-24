from abc import abstractmethod, ABC
from typing import final, Callable

from WinCopies.Collections.Linked.Doubly import DoublyLinkedNode
from WinCopies.Collections.Abstraction.Linked import IterableStack

type EventHandler[TSender, TArgs] = Callable[[TSender, TArgs], None]

class IEventCookie(ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Remove(self) -> None:
        pass

class IReadOnlyEventManager[TSender, TArgs](ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Invoke(self, sender: TSender, args: TArgs) -> bool:
        pass
class IWriteOnlyEventManager[TSender, TArgs, TCookie](ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, handler: EventHandler[TSender, TArgs]) -> TCookie:
        pass

class IEventManager[TSender, TArgs](IReadOnlyEventManager[TSender, TArgs], IWriteOnlyEventManager[TSender, TArgs, IEventCookie]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, handler: EventHandler[TSender, TArgs]) -> IEventCookie:
        pass

class EventManager[TSender, TArgs](IEventManager[TSender, TArgs]):
    class __EventCookie(IEventCookie):
        def __init__(self, node: DoublyLinkedNode[EventHandler[TSender, TArgs]]):
            super().__init__()

            self.__node: DoublyLinkedNode[EventHandler[TSender, TArgs]] = node
        
        @final
        def Remove(self) -> None:
            self.__node.Remove()
    
    def __init__(self):
        self.__events = IterableStack[EventHandler[TSender, TArgs]]()
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> IEventCookie:
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
        self.__manager = manager
    
    @final
    def Invoke(self, sender: TSender, args: TArgs) -> bool:
        return self.__manager.Invoke(sender, args)
class WriteOnlyEventManager[TSender, TArgs](IWriteOnlyEventManager[TSender, TArgs]):
    def __init__(self, manager: IReadOnlyEventManager[TSender, TArgs]):
        self.__manager = manager
    
    @final
    def Add(self, handler: EventHandler[TSender, TArgs]) -> None:
        self.__manager.Add(handler)