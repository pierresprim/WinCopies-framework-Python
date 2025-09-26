from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.IO import IDirEntry
from WinCopies.IO.DirEntry import DirEntry

def Enumerate(dirEntry: IDirEntry) -> Generator[IDirEntry]:
    for dirEntry in dirEntry.GetRecursiveEnumerator().AsIterator():
        yield dirEntry

def TryGetEnumeratorFromPath(path: str) -> IEnumerator[IDirEntry]|None:
    return DirEntry.FromPath(path).TryGetRecursiveEnumerator()
def GetEnumeratorFromPath(path: str) -> IEnumerator[IDirEntry]:
    return DirEntry.FromPath(path).GetRecursiveEnumerator()

def EnumerateFromPath(path: str) -> Generator[IDirEntry]:
    return Enumerate(DirEntry.FromPath(path))