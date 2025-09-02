from collections.abc import Iterator

from WinCopies.Collections import Generator
from WinCopies.IO import IDirEntry
from WinCopies.IO.DirEntry import DirEntry

def Enumerate(dirEntry: IDirEntry) -> Generator[IDirEntry]:
    for dirEntry in dirEntry.GetRecursiveIterator():
        yield dirEntry

def TryGetIteratorFromPath(path: str) -> Iterator[IDirEntry]|None:
    return DirEntry.FromPath(path).TryGetRecursiveIterator()
def GetIteratorFromPath(path: str) -> Iterator[IDirEntry]:
    return DirEntry.FromPath(path).GetRecursiveIterator()

def EnumerateFromPath(path: str) -> Generator[IDirEntry]:
    return Enumerate(DirEntry.FromPath(path))