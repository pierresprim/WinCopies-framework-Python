from __future__ import annotations

from typing import final
from xml.etree.ElementTree import Element, iterparse

from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, IteratorProvider, AsEnumerator
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyScannable
from WinCopies.Collections.Enumeration.Recursive.Scannable import Events, IGeneratorProvider, RecursivelyIteratorProvider, ManagedGeneratorProvider
from WinCopies.Enum import EnumerateFieldNames, TryConvertFromString
from WinCopies.IO.Stream import IStreamReader, ITextStreamReader
from WinCopies.Serialization import TextDataReader
from WinCopies.Typing.Pairing import IKeyValuePair, CreateDualResult

def GetGenerator(stream: IStreamReader[str], events: Events) -> Generator[IKeyValuePair[Element, Events]]:
    event: Events|None = None

    for item in iterparse(stream.AsReader(), events=tuple(event.lower() for event in EnumerateFieldNames(events))):
        if (event := TryConvertFromString(Events, item[0], lambda name, value: name is not None and name.lower() == value.lower())) is not None: yield CreateDualResult(item[1], event)
def GetEnumerator(stream: ITextStreamReader, events: Events) -> IEnumerator[IKeyValuePair[Element, Events]]:
    return AsEnumerator(GetGenerator(stream, events))
def GetEnumerable(stream: ITextStreamReader, events: Events) -> IEnumerable[IKeyValuePair[Element, Events]]:
    return IteratorProvider[IKeyValuePair[Element, Events]](lambda: GetGenerator(stream, events))

class Reader(TextDataReader[Element]):
    class _Enumerable(RecursivelyIteratorProvider[Element]):
        class _GeneratorProvider(ManagedGeneratorProvider[Element]):
            def __init__(self) -> None: super().__init__()
            
            def DisposeItem(self, item: Element) -> None: item.clear()
        
        def __init__(self, stream: IStreamReader[str]) -> None:
            super().__init__()

            self.__stream: IStreamReader[str] = stream
        
        @final
        def _GetStream(self) -> IStreamReader[str]:
            return self.__stream
        
        @final
        def _GetGeneratorProvider(self) -> IGeneratorProvider[Element]:
            return Reader._Enumerable._GeneratorProvider()
        
        @final
        def _GetItemsIterator(self, events: Events) -> Generator[IKeyValuePair[Element, Events]]:
            return GetGenerator(self._GetStream(), events)
    
    def __init__(self, stream: ITextStreamReader) -> None: super().__init__(stream)
    
    @final
    def _Parse(self, stream: IStreamReader[str]) -> IRecursivelyScannable[Element]:
        return Reader._Enumerable(stream)