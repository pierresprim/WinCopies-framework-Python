from weakref import WeakKeyDictionary as WeakKeyDictionaryBase, WeakValueDictionary as WeakValueDictionaryBase

from WinCopies.Collections.Abstraction.Collection.Mapping import Dictionary
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Typing.Comparison import HashableProtocol

class WeakKeyDictionary[TKey: HashableProtocol, TValue](Dictionary[TKey, TValue]):
    def __init__(self, dictionary: WeakKeyDictionaryBase[TKey, TValue]|None = None) -> None:
        super().__init__(WeakKeyDictionaryBase[TKey, TValue]() if dictionary is None else dictionary)
class WeakValueDictionary[TKey: HashableProtocol, TValue](Dictionary[TKey, TValue]):
    def __init__(self, dictionary: WeakValueDictionaryBase[TKey, TValue]|None = None) -> None:
        super().__init__(WeakValueDictionaryBase[TKey, TValue]() if dictionary is None else dictionary)

def CreateWeakKeyDictionary[TKey: HashableProtocol, TValue](dictionary: WeakKeyDictionaryBase[TKey, TValue]|None = None) -> IDictionary[TKey, TValue]:
    """
    Returns an IDictionary whose keys are held by weak reference. Entries vanish
    automatically when the key is no longer strongly referenced elsewhere.
    
    TKey must be a weakref-compatible Python object (i.e. supports __weakref__).
    Primitive types like int, str, tuple, frozenset are not supported.
    
    Iteration safety: changes triggered by garbage collection during iteration are
    handled transparently by the underlying weakref.WeakKeyDictionary.
    """
    return WeakKeyDictionary[TKey, TValue](dictionary)
def CreateWeakValueDictionary[TKey: HashableProtocol, TValue](dictionary: WeakValueDictionaryBase[TKey, TValue]|None = None) -> IDictionary[TKey, TValue]:
    """
    Returns an IDictionary whose values are held by weak reference. Entries vanish
    automatically when the value is no longer strongly referenced elsewhere.
    
    TValue must be a weakref-compatible Python object (i.e. supports __weakref__).
    Primitive types like int, str, tuple, frozenset are not supported.
    
    Iteration safety: changes triggered by garbage collection during iteration are
    handled transparently by the underlying weakref.WeakValueDictionary.
    """
    return WeakValueDictionary[TKey, TValue](dictionary)