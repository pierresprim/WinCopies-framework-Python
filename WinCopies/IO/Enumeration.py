from collections.abc import Iterator

from WinCopies.Collections import Generator, Enumeration
from WinCopies.Collections.Enumeration import IEnumerator, EmptyEnumerator, RecursiveEnumerator
from WinCopies.IO import IDirEntry
from WinCopies.IO.DirEntry import DirEntry

def TryGetEnumerator(dirEntry: IDirEntry) -> IEnumerator[IDirEntry]|None:
    iterator: Iterator[IDirEntry]|None = dirEntry.TryGetIterator()

    return None if iterator is None else RecursiveEnumerator[IDirEntry](Enumeration.FromIterator(iterator))
def GetEnumerator(dirEntry: IDirEntry) -> IEnumerator[IDirEntry]:
    enumerator: IEnumerator[IDirEntry]|None = TryGetEnumerator(dirEntry)
    
    return EmptyEnumerator[IDirEntry]() if enumerator is None else enumerator

def Enumerate(dirEntry: IDirEntry) -> Generator[IDirEntry]:
    for dirEntry in GetEnumerator(dirEntry):
        yield dirEntry

def TryGetEnumeratorFromPath(path: str) -> IEnumerator[IDirEntry]|None:
    return TryGetEnumerator(DirEntry.FromPath(path))
def GetEnumeratorFromPath(path: str) -> IEnumerator[IDirEntry]:
    return GetEnumerator(DirEntry.FromPath(path))

def EnumerateFromPath(path: str) -> Generator[IDirEntry]:
    return Enumerate(DirEntry.FromPath(path))