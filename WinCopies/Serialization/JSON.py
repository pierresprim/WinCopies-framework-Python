from __future__ import annotations

from abc import abstractmethod
from enum import Enum, Flag
from typing import Callable, final

from WinCopies import Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction.Collection import Tuple
from WinCopies.Collections.Abstraction.Collection.Mapping import Dictionary
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IEnumerator, AbstractionEnumerator, EnumeratorProvider, IteratorProvider, AsEnumerator, GetEnumeratorInactiveError
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyScannable
from WinCopies.Collections.Enumeration.Recursive.Scannable import Events, IGeneratorProvider, RecursivelyIteratorProvider, ObjectGeneratorProvider
from WinCopies.Collections.Extensions import ITuple, IReadOnlyDictionary, IDictionary
from WinCopies.Collections.Linked.Singly import IQueue, Queue
from WinCopies.Delegates import BoolFalse
from WinCopies.IO.Stream import IStreamReader, IBinaryStreamReader
from WinCopies.Serialization import BinaryDataReader
from WinCopies.Typing import IDisposable, INullable, GetNullable, GetNullValue, GetDisposedError
from WinCopies.Typing.Delegate import Function, Method
from WinCopies.Typing.Object import IString, String
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult, CreateDualResult

from ijson import parse

class Event(Enum):
    NoEvent = 0
    StartMap = 1
    EndMap = 2
    StartArray = 3
    EndArray = 4
    MapKey = 5
    NullValue = 6
    Boolean = 7
    Integer = 8
    Double = 9
    Number = 10
    String = 11

class _Events:
    START_MAP = "start_map"
    END_MAP = "end_map"
    START_ARRAY = "start_array"
    END_ARRAY = "end_array"
    MAP_KEY = "map_key"
    NULL = "null"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DOUBLE = "double"
    NUMBER = "number"
    STRING = "string"

    @staticmethod
    def TryConvertToEvent(eventName: str) -> Event|None:
        match eventName:
            case _Events.START_MAP: return Event.StartMap
            case _Events.END_MAP: return Event.EndMap
            
            case _Events.START_ARRAY: return Event.StartArray
            case _Events.END_ARRAY: return Event.EndArray
            
            case _Events.MAP_KEY: return Event.MapKey
            
            case _Events.NULL: return Event.NullValue
            
            case _Events.BOOLEAN: return Event.Boolean
            case _Events.INTEGER: return Event.Integer
            case _Events.DOUBLE: return Event.Double
            case _Events.NUMBER: return Event.Number
            case _Events.STRING: return Event.String
            
            case _: return None

class ValueType(Enum):
    NotApplicable = 0
    Null = 1
    Boolean = 2
    Integer = 3
    Double = 4
    Number = 5
    String = 6

class NodeAttributes(Flag):
    Null = 0
    Root = 1
    Dictionary = 2

class INode(IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetAttributes(self) -> NodeAttributes:
        ...
    
    @abstractmethod
    def GetPath(self) -> str:
        ...

    @abstractmethod
    def TryGetValues(self) -> ICountableEnumerable[DualResult[object, ValueType]]|None:
        ...

class IArrayNode(INode):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryGetValues(self) -> ITuple[DualResult[object, ValueType]]|None:
        ...
class IDictionaryNode(INode):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetItems(self) -> IReadOnlyDictionary[IString, DualResult[object, ValueType]]|None:
        ...

class _BufferBase(Abstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetValues(self) -> ICountableEnumerable[DualResult[object, ValueType]]|None:
        ...
class _Buffer[T](_BufferBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Initialize(self, items: T) -> None:
        ...

class _ArrayBufferBase(_Buffer[ITuple[DualResult[object, ValueType]]]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetValues(self) -> ITuple[DualResult[object, ValueType]]|None:
        ...
class _DictionaryBufferBase(_Buffer[IReadOnlyDictionary[IString, DualResult[object, ValueType]]]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetItems(self) -> IReadOnlyDictionary[IString, DualResult[object, ValueType]]|None:
        ...

@final
class _ArrayBuffer(_ArrayBufferBase):
    def __init__(self) -> None:
        super().__init__()

        self.__items: ITuple[DualResult[object, ValueType]]|None = None
    
    def Initialize(self, items: ITuple[DualResult[object, ValueType]]) -> None: self.__items = items
    
    def TryGetValues(self) -> ITuple[DualResult[object, ValueType]]|None: return self.__items
@final
class _DictionaryBuffer(_DictionaryBufferBase):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IReadOnlyDictionary[IString, DualResult[object, ValueType]]|None = None
    
    def Initialize(self, items: IReadOnlyDictionary[IString, DualResult[object, ValueType]]) -> None: self.__items = items
    
    def TryGetValues(self) -> ICountableEnumerable[DualResult[object, ValueType]]|None:
        items: IReadOnlyDictionary[IString, DualResult[object, ValueType]]|None = self.TryGetItems()

        return None if items is None else items.GetValues()
    
    def TryGetItems(self) -> IReadOnlyDictionary[IString, DualResult[object, ValueType]]|None: return self.__items

@final
class _NullArrayBuffer(_ArrayBufferBase):
    def __init__(self) -> None: super().__init__()
    
    def Initialize(self, items: ITuple[DualResult[object, ValueType]]) -> None: raise GetDisposedError()
    
    def TryGetValues(self) -> ITuple[DualResult[object, ValueType]]|None: return None
@final
class _NullDictionaryBuffer(_DictionaryBufferBase):
    def __init__(self) -> None: super().__init__()
    
    def Initialize(self, items: IReadOnlyDictionary[IString, DualResult[object, ValueType]]) -> None: raise GetDisposedError()
    
    def TryGetValues(self) -> ITuple[DualResult[object, ValueType]]|None: return None
    
    def TryGetItems(self) -> IReadOnlyDictionary[IString, DualResult[object, ValueType]]|None: return None

_arrayBuffer: _ArrayBufferBase = _NullArrayBuffer()
_dictionaryBuffer: _DictionaryBufferBase = _NullDictionaryBuffer()

class _HandlerBase(Abstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Append(self, key: str, value: DualResult[object, ValueType]) -> None:
        ...
    
    @abstractmethod
    def Flush(self) -> None:
        ...

    @abstractmethod
    def GetNode(self) -> INode:
        ...
class _Handler[T: _BufferBase](_HandlerBase):
    def __init__(self) -> None:
        super().__init__()

        self.__buffer: T = self._CreateBuffer()
    
    @abstractmethod
    def _CreateBuffer(self) -> T:
        ...

    @final
    def _GetBuffer(self) -> T:
        return self.__buffer

class _Tuple(_Handler[_ArrayBuffer]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IQueue[DualResult[object, ValueType]] = Queue[DualResult[object, ValueType]]()
    
    @final
    def _CreateBuffer(self) -> _ArrayBuffer:
        return _ArrayBuffer()
    
    @final
    def Append(self, key: str, value: DualResult[object, ValueType]) -> None: self.__items.Push(value)
    
    @final
    def Flush(self) -> None: self._GetBuffer().Initialize(Tuple[DualResult[object, ValueType]](self.__items.AsGenerator()))
class _Dictionary(_Handler[_DictionaryBuffer]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IDictionary[IString, DualResult[object, ValueType]] = Dictionary[IString, DualResult[object, ValueType]]()
    
    @final
    def _CreateBuffer(self) -> _DictionaryBuffer:
        return _DictionaryBuffer()
    
    @final
    def Append(self, key: str, value: DualResult[object, ValueType]) -> None: self.__items.Add(String(key), value)
    
    @final
    def Flush(self) -> None: self._GetBuffer().Initialize(self.__items.AsReadOnly())

@final
class _RootTuple(_Tuple):
    def __init__(self) -> None:
        super().__init__()

        self.__root: IArrayNode = _RootArray(self._GetBuffer())
    
    @final
    def GetNode(self) -> INode: return self.__root
@final
class _RootDictionary(_Dictionary):
    def __init__(self) -> None:
        super().__init__()

        self.__root: INode = _Root(self._GetBuffer())
    
    @final
    def GetNode(self) -> INode: return self.__root

@final
class _NodeTuple(_Tuple):
    def __init__(self, path: str) -> None:
        super().__init__()

        self.__node: IArrayNode = _ArrayNode(path, self._GetBuffer())
    
    @final
    def GetNode(self) -> INode: return self.__node
@final
class _NodeDictionary(_Dictionary):
    def __init__(self, path: str) -> None:
        super().__init__()

        self.__node: INode = _Node(path, self._GetBuffer())
    
    @final
    def GetNode(self) -> INode: return self.__node

class _NodeAbstract[T: _BufferBase](Abstract, INode):
    def __init__(self, buffer: T) -> None:
        super().__init__()

        self.__buffer: T = buffer
    
    @abstractmethod
    def _GetDefaultBuffer(self) -> T:
        ...
    
    @final
    def _GetBuffer(self) -> T:
        return self.__buffer
    
    def Dispose(self) -> None: self.__buffer = self._GetDefaultBuffer()

class _RootBase[T: _BufferBase](_NodeAbstract[T]):
    def __init__(self, buffer: T) -> None: super().__init__(buffer)
    
    @final
    def GetPath(self) -> str: return ''

class _Root(_RootBase[_DictionaryBufferBase], IDictionaryNode):
    def __init__(self, buffer: _DictionaryBufferBase) -> None: super().__init__(buffer)
    
    @final
    def GetAttributes(self) -> NodeAttributes: return NodeAttributes.Root | NodeAttributes.Dictionary
    
    @final
    def TryGetValues(self) -> ICountableEnumerable[DualResult[object, ValueType]]|None: return self._GetBuffer().TryGetValues()
    @final
    def TryGetItems(self) -> IReadOnlyDictionary[IString, DualResult[object, ValueType]]|None: return self._GetBuffer().TryGetItems()
    
    @final
    def _GetDefaultBuffer(self) -> _DictionaryBufferBase:
        return _dictionaryBuffer
class _RootArray(_RootBase[_ArrayBufferBase], IArrayNode):
    def __init__(self, buffer: _ArrayBufferBase) -> None: super().__init__(buffer)
    
    @final
    def GetAttributes(self) -> NodeAttributes: return NodeAttributes.Root
    
    @final
    def TryGetValues(self) -> ITuple[DualResult[object, ValueType]]|None: return self._GetBuffer().TryGetValues()
    
    @final
    def _GetDefaultBuffer(self) -> _ArrayBufferBase:
        return _arrayBuffer

class _NodeBase[T: _BufferBase](_NodeAbstract[T]):
    def __init__(self, path: str, buffer: T) -> None:
        super().__init__(buffer)

        self.__path: str = path
    
    @final
    def IsRoot(self) -> bool: return False
    
    @final
    def GetPath(self) -> str: return self.__path

class _Node(_NodeBase[_DictionaryBufferBase], IDictionaryNode):
    def __init__(self, path: str, buffer: _DictionaryBuffer) -> None: super().__init__(path, buffer)
    
    @final
    def GetAttributes(self) -> NodeAttributes: return NodeAttributes.Dictionary
    
    @final
    def TryGetValues(self) -> ICountableEnumerable[DualResult[object, ValueType]]|None: return self._GetBuffer().TryGetValues()
    @final
    def TryGetItems(self) -> IReadOnlyDictionary[IString, DualResult[object, ValueType]]|None: return self._GetBuffer().TryGetItems()
    
    @final
    def _GetDefaultBuffer(self) -> _DictionaryBufferBase:
        return _dictionaryBuffer
class _ArrayNode(_NodeBase[_ArrayBufferBase], IArrayNode):
    def __init__(self, path: str, buffer: _ArrayBufferBase) -> None: super().__init__(path, buffer)
    
    @final
    def GetAttributes(self) -> NodeAttributes: return NodeAttributes.Null
    
    @final
    def TryGetValues(self) -> ITuple[DualResult[object, ValueType]]|None: return self._GetBuffer().TryGetValues()
    
    @final
    def _GetDefaultBuffer(self) -> _ArrayBufferBase:
        return _arrayBuffer

class _GeneratorAbstract(Abstract):
    def __init__(self) -> None: super().__init__()
    
    def _GetResult(self, generator: _GeneratorAbstract, event: Event, updater: Method[_GeneratorAbstract]) -> INullable[DualResult[INode|None, Event]]:
        updater(generator)

        return GetNullable(DualResult[INode|None, Event](generator.TryGetNode(), event))
    def _SetResult(self, key: str, value: object, event: Event, handler: _HandlerBase) -> None:
        def append(value: DualResult[object, ValueType]) -> None: handler.Append(key, value)
        
        def handle(value: object) -> None:
            def getType() -> ValueType:
                match event:
                    case Event.Boolean: return ValueType.Boolean
                    case Event.Integer: return ValueType.Integer
                    case Event.Double: return ValueType.Double
                    case Event.Number: return ValueType.Number
                    case Event.String: return ValueType.String
                    
                    case _: return ValueType.NotApplicable
            
            valueType: ValueType = getType()

            if valueType.value > ValueType.NotApplicable.value: append(CreateDualResult(value, valueType))
        
        match event:
            case Event.NullValue: append(CreateDualResult(None, ValueType.Null))
            
            case _: handle(value)

    @abstractmethod
    def TryGetNode(self) -> INode|None:
        ...

    @abstractmethod
    def MoveNext(self, nextItemProvider: Function[Item|None], updater: Method[_GeneratorAbstract]) -> INullable[DualResult[INode|None, Event]]|None:
        ...
    
    @abstractmethod
    def Start(self, path: str) -> _GeneratorAbstract:
        ...
    @abstractmethod
    def StartArray(self, path: str) -> _GeneratorAbstract:
        ...

    @abstractmethod
    def End(self) -> _GeneratorAbstract:
        ...

class _GeneratorInitializer(_GeneratorAbstract):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNext: Callable[[Function[Item|None], Method[_GeneratorAbstract]], INullable[DualResult[INode|None, Event]]|None] = self.__MoveNext
    
    @final
    def __MoveNext(self, nextItemProvider: Function[Item|None], updater: Method[_GeneratorAbstract]) -> INullable[DualResult[INode|None, Event]]|None:
        def moveNext(key: str, value: object, event: Event, generator: _GeneratorBase) -> INullable[DualResult[INode|None, Event]]|None:
            self._SetResult(key, value, event, generator.GetHandler())

            updater(generator)
            
            self.__moveNext = self.__MoveNext

            return GetNullValue()
        
        def getResult(generator: _GeneratorAbstract, event: Event) -> INullable[DualResult[INode|None, Event]]: return self._GetResult(generator, event, updater)
        
        item: Item|None = nextItemProvider()

        if item is None: return None
        
        key: str = item.GetKey()
        event: Event = item.GetEvent()
        
        match event:
            case Event.StartMap: return getResult(self.Start(key), event)
            case Event.StartArray: return getResult(self.StartArray(key), event)
            
            case Event.EndMap | Event.EndArray: return GetNullable(CreateDualResult(None, event))
            
            case _:
                generator: _GeneratorBase = self.StartArray(key)

                self.__moveNext = lambda nextItemProvider, updater: moveNext(key, item.GetValue(), event, generator)

                return GetNullable(CreateDualResult(generator.TryGetNode(), Event.StartArray))
        
        return None
    
    @final
    def TryGetNode(self) -> INode|None: return None
    
    @final
    def MoveNext(self, nextItemProvider: Function[Item|None], updater: Method[_GeneratorAbstract]) -> INullable[DualResult[INode|None, Event]]|None: return self.__moveNext(nextItemProvider, updater)
    
    @final
    def Start(self, path: str) -> _GeneratorBase: return _RootGenerator(self)
    @final
    def StartArray(self, path: str) -> _GeneratorBase: return _RootArrayGenerator(self)
    
    @final
    def End(self) -> _GeneratorAbstract: return self

class _GeneratorBase(_GeneratorAbstract):
    def __init__(self, parent: _GeneratorAbstract) -> None:
        super().__init__()

        self.__parent: _GeneratorAbstract = parent

    @abstractmethod
    def GetHandler(self) -> _HandlerBase:
        ...

    @final
    def TryGetNode(self) -> INode: return self.GetHandler().GetNode()
    
    @final
    def MoveNext(self, nextItemProvider: Function[Item|None], updater: Method[_GeneratorAbstract]) -> INullable[DualResult[INode|None, Event]]|None:
        def getResult(generator: _GeneratorAbstract, event: Event) -> INullable[DualResult[INode|None, Event]]: return self._GetResult(generator, event, updater)
        
        item: Item|None = nextItemProvider()

        if item is None: return None
        
        key: str = item.GetKey()
        event: Event = item.GetEvent()
        
        match event:
            case Event.StartMap: return getResult(self.Start(key), event)
            case Event.StartArray: return getResult(self.StartArray(key), event)
            
            case Event.EndMap | Event.EndArray: return getResult(self.End(), event)
            
            case _: self._SetResult(key, item.GetValue(), event, self.GetHandler())
        
        return GetNullValue()
    
    @final
    def Start(self, path: str) -> _GeneratorAbstract: return _NodeGenerator(path, self)
    @final
    def StartArray(self, path: str) -> _GeneratorAbstract: return _ArrayNodeGenerator(path, self)
    
    @final
    def End(self) -> _GeneratorAbstract:
        self.GetHandler().Flush()
        
        return self.__parent

class _RootGeneratorBase[T: _HandlerBase](_GeneratorBase):
    def __init__(self, parent: _GeneratorAbstract) -> None:
        super().__init__(parent)

        self.__handler: T = self._CreateHandler()
    
    @abstractmethod
    def _CreateHandler(self) -> T:
        ...

    @final
    def GetHandler(self) -> T: return self.__handler

class _RootGenerator(_RootGeneratorBase[_RootDictionary]):
    def __init__(self, initializer: _GeneratorInitializer) -> None: super().__init__(initializer)
    
    @final
    def _CreateHandler(self) -> _RootDictionary:
        return _RootDictionary()
class _RootArrayGenerator(_RootGeneratorBase[_RootTuple]):
    def __init__(self, initializer: _GeneratorInitializer) -> None: super().__init__(initializer)
    
    @final
    def _CreateHandler(self) -> _RootTuple:
        return _RootTuple()

class _NodeGeneratorBase[T: _HandlerBase](_GeneratorBase):
    def __init__(self, path: str, parent: _GeneratorAbstract) -> None:
        super().__init__(parent)

        self.__handler: T = self._CreateHandler(path)
    
    @abstractmethod
    def _CreateHandler(self, path: str) -> T:
        ...

    @final
    def GetHandler(self) -> T: return self.__handler

class _NodeGenerator(_NodeGeneratorBase[_NodeDictionary]):
    def __init__(self, path: str, parent: _GeneratorAbstract) -> None: super().__init__(path, parent)
    
    @final
    def _CreateHandler(self, path: str) -> _NodeDictionary:
        return _NodeDictionary(path)
class _ArrayNodeGenerator(_NodeGeneratorBase[_NodeTuple]):
    def __init__(self, path: str, parent: _GeneratorAbstract) -> None: super().__init__(path, parent)
    
    @final
    def _CreateHandler(self, path: str) -> _NodeTuple:
        return _NodeTuple(path)

class Item(Abstract):
    def __init__(self, key: str, value: object, event: Event) -> None:
        super().__init__()

        self.__key: str = key
        self.__value: object = value
        self.__event: Event = event
    
    @final
    def GetKey(self) -> str: return self.__key
    @final
    def GetValue(self) -> object: return self.__value
    
    @final
    def GetEvent(self) -> Event: return self.__event

class Enumerator(AbstractionEnumerator[Item, DualResult[INode|None, Event]]):
    def __init__(self, enumerator: IEnumerator[Item]) -> None:
        def getNext() -> Item|None: return self._GetContainer().GetCurrent() if self.__MoveNextBase() else None
        def update(generator: _GeneratorAbstract) -> None: self.__generator = generator

        super().__init__(enumerator)

        self.__current: DualResult[INode|None, Event]|None = None
        self.__generator: _GeneratorAbstract = _GeneratorInitializer() # type: ignore[no-redef]
        self.__moveNext: Function[bool] = BoolFalse
        self.__nextItemProvider: Function[Item|None] = getNext
        self.__updater: Method[_GeneratorAbstract] = update
    
    @final
    def __MoveNextBase(self) -> bool:
        return super()._MoveNextOverride()
    
    @final
    def _GetCurrent(self) -> DualResult[INode|None, Event]:
        current: DualResult[INode|None, Event]|None = self.__current

        if current is None: raise GetEnumeratorInactiveError()
        
        return current
    
    def _OnStarting(self) -> bool:
        def moveNext() -> bool:
            def getResult() -> INullable[DualResult[INode|None, Event]]|None: return self.__generator.MoveNext(self.__nextItemProvider, self.__updater)
            
            result: INullable[DualResult[INode|None, Event]]|None = getResult()

            while result is not None:
                if result.HasValue():
                    self.__current = result.GetValue()

                    return True
                
                result = getResult()
            
            return False
        
        if super()._OnStarting():
            self.__moveNext = lambda: moveNext()
    
            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool: return self.__moveNext()
    
    def _OnEnded(self) -> None: self.__current = None
    def _OnStopped(self) -> None: pass
    
    def _ResetOverride(self) -> bool: return self._GetContainer().TryReset() is True

def _Enumerate(stream: IStreamReader[bytes]) -> Generator[Item]:
    event: Event|None = None

    for item in parse(stream.AsReader()):
        if (event := _Events.TryConvertToEvent(item[1])) is not None: yield Item(str(item[0]), item[2], event)

def GetNodeEnumerator(stream: IStreamReader[bytes]) -> IEnumerator[DualResult[INode|None, Event]]:
    return Enumerator(AsEnumerator(_Enumerate(stream)))
def Enumerate(stream: IStreamReader[bytes]) -> IEnumerable[DualResult[INode|None, Event]]:
    return EnumeratorProvider[DualResult[INode|None, Event]](lambda: GetNodeEnumerator(stream))

def GetGenerator(stream: IStreamReader[bytes], events: Events) -> Generator[IKeyValuePair[INode, Events]]:
    def tryGetEvent(event: Event) -> Events|None:
        match event:
            case Event.StartMap | Event.StartArray: return Events.Start
            case Event.EndMap | Event.EndArray: return Events.End
            
            case _: return None
    
    node: INode|None = None
    event: Events|None = None

    for item in GetNodeEnumerator(stream).AsIterator():
        if (event := tryGetEvent(item.GetValue())) is not None and (node := item.GetKey()) is not None and event in events: yield CreateDualResult(node, event)
def GetEnumerator(stream: IStreamReader[bytes], events: Events) -> IEnumerator[IKeyValuePair[INode, Events]]:
    return AsEnumerator(GetGenerator(stream, events))
def GetEnumerable(stream: IStreamReader[bytes], events: Events) -> IEnumerable[IKeyValuePair[INode, Events]]:
    return IteratorProvider[IKeyValuePair[INode, Events]](lambda: GetGenerator(stream, events))

class Reader(BinaryDataReader[INode]):
    class _Enumerable(RecursivelyIteratorProvider[INode]):
        class _GeneratorProvider(ObjectGeneratorProvider[INode]):
            def __init__(self) -> None: super().__init__()
            
            def DisposeItem(self, item: INode) -> None: item.Dispose()
        
        def __init__(self, stream: IStreamReader[bytes]) -> None:
            super().__init__()

            self.__stream: IStreamReader[bytes] = stream
        
        @final
        def _GetGeneratorProvider(self) -> IGeneratorProvider[INode]:
            return Reader._Enumerable._GeneratorProvider()
        
        @final
        def _GetItemsIterator(self, events: Events) -> Generator[IKeyValuePair[INode, Events]]:
            return GetGenerator(self.__stream, events)
    
    def __init__(self, stream: IBinaryStreamReader) -> None: super().__init__(stream)
    
    @final
    def _Parse(self, stream: IStreamReader[bytes]) -> IRecursivelyScannable[INode]:
        return Reader._Enumerable(stream)