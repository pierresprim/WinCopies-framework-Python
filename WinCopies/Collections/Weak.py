from weakref import WeakValueDictionary, WeakKeyDictionary

from WinCopies.Collections.Abstraction.Collection.Mapping import CreateDictionary
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Typing.Comparison import IHashableValue

def CreateWeakKeyDictionary[TKey: IHashableValue, TValue](dictionary: WeakKeyDictionary[TKey, TValue]|None = None) -> IDictionary[TKey, TValue]:
    """
    Returns an IDictionary whose keys are held by weak reference. Entries vanish
    automatically when the key is no longer strongly referenced elsewhere.
    
    TKey must be a weakref-compatible Python object (i.e. supports __weakref__).
    Primitive types like int, str, tuple, frozenset are not supported.
    
    Iteration safety: changes triggered by garbage collection during iteration are
    handled transparently by the underlying weakref.WeakKeyDictionary.
    """
    return CreateDictionary(WeakKeyDictionary[TKey, TValue]() if dictionary is None else dictionary)
def CreateWeakValueDictionary[TKey: IHashableValue, TValue](dictionary: WeakValueDictionary[TKey, TValue]|None = None) -> IDictionary[TKey, TValue]:
    """
    Returns an IDictionary whose values are held by weak reference. Entries vanish
    automatically when the value is no longer strongly referenced elsewhere.
    
    TValue must be a weakref-compatible Python object (i.e. supports __weakref__).
    Primitive types like int, str, tuple, frozenset are not supported.
    
    Iteration safety: changes triggered by garbage collection during iteration are
    handled transparently by the underlying weakref.WeakValueDictionary.
    """
    return CreateDictionary(WeakValueDictionary[TKey, TValue]() if dictionary is None else dictionary)