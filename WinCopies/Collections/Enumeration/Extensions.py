# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 02:12:00 2025

@author: Pierre Sprimont
"""

from abc import abstractmethod
from typing import final



from WinCopies import IInterface

from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, Enumerable, EnumeratorBase, AbstractionEnumerator, GetNullEnumerable
from WinCopies.Collections.Linked.Doubly import IList, List, IDoublyLinkedNode

from WinCopies.Typing.Delegate import Converter, Function
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class IterableBuilder[T](Enumerable[T]):
    @final
    class __Iterable(Enumerable[T]):
        @final
        class __Iterable(Enumerable[T]):
            @final
            class __Enumerator(AbstractionEnumerator[T, T]):
                @final
                class __Enumerator(EnumeratorBase[T]):
                    class IToken(IInterface):
                        def __init__(self):
                            super().__init__()
                        
                        @abstractmethod
                        def GetCurrent(self) -> T|None:
                            pass
                        
                        @abstractmethod
                        def MoveNext(self) -> bool:
                            pass
                    @final
                    class __NullToken(IToken):
                        def __init__(self):
                            super().__init__()
                        
                        def GetCurrent(self) -> T|None:
                            return None
                        
                        def MoveNext(self) -> bool:
                            return False
                    @final
                    class Token(IToken):
                        def __init__(self, node: IDoublyLinkedNode[T]):
                            def moveNext() -> bool:
                                def moveNext() -> bool:
                                    if self.__node is None:
                                        return False
                                    
                                    else:
                                        self.__node = self.__node.GetNext()

                                        return self.__node is not None
                                
                                self.__moveNext = moveNext

                                return True

                            super().__init__()

                            self.__node: IDoublyLinkedNode[T]|None = node
                            self.__moveNext: Function[bool] = moveNext
                        
                        def GetCurrent(self) -> T|None:
                            return None if self.__node is None else self.__node.GetValue()
                        
                        def MoveNext(self) -> bool:
                            return self.__moveNext()
                    
                    @final
                    class __Enumerator(IInterface):
                        def __init__(self, enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator):
                            super().__init__()

                            self.__enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator = enumerator
                        
                        def GetFirst(self) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken:
                            return self.__enumerator.GetFirst() # type: ignore
                        
                        def GetCurrent(self) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken:
                            return self.__enumerator.GetToken() # type: ignore
                        
                        def MoveNext(self) -> bool:
                            return self.__enumerator.MoveNext()
                    
                    def __init__(self, enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator):
                        super().__init__()

                        self.__enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.__Enumerator = IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.__Enumerator(enumerator)
                        self.__token: IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken = enumerator.GetFirst() # type: ignore
                    
                    def IsResetSupported(self) -> bool:
                        return True
                    
                    def GetCurrent(self) -> T|None:
                        return self.__token.GetCurrent()
                    
                    def _MoveNextOverride(self) -> bool:
                        if self.__token.MoveNext():
                            return True
                        
                        if self.__enumerator.MoveNext():
                            self.__token = self.__enumerator.GetCurrent()

                            return True
                        
                        return False
                    
                    def _OnStopped(self) -> None:
                        self.__token = IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.__NullToken()
                    
                    def _ResetOverride(self) -> bool:
                        self.__token = self.__enumerator.GetFirst()

                        return True
                
                def __init__(self, builder: IterableBuilder[T], enumerator: IEnumerator[T]):
                    super().__init__(enumerator)

                    self.__builder: IterableBuilder[T] = builder
                    self.__items: IList[T] = None # type: ignore
                    self.__getEnumerator: Function[IEnumerator[T]] = None # type: ignore
                
                def __GetEnumerator(self) -> IEnumerator[T]:
                    self.__getEnumerator = lambda: IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator(self)

                    return self
                
                def GetItemEnumerator(self) -> IEnumerator[T]:
                    return self.__getEnumerator()
                
                def GetCurrent(self) -> T|None:
                    return self.__items.TryGetLastValueOrNone()
                
                def __GetToken(self, func: Converter[IList[T], IDoublyLinkedNode[T]|None]) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken|None:
                    node: IDoublyLinkedNode[T]|None = func(self.__items)

                    return None if node is None else IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.Token(node)
                
                def GetFirst(self) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken|None:
                    return self.__GetToken(lambda items: items.GetFirst())
                def GetToken(self) -> IterableBuilder[T].__Iterable.__Iterable.__Enumerator.__Enumerator.IToken|None:
                    return self.__GetToken(lambda items: items.GetLast())
                
                def _OnStarting(self) -> bool:
                    if super()._OnStarting():
                        self.__getEnumerator = self.__GetEnumerator
                        self.__items: IList[T] = List[T]()

                        return True
                    
                    return False
                
                def _MoveNextOverride(self) -> bool:
                    if super()._MoveNextOverride():
                        value: T|None = self.GetCurrent()

                        if value is None:
                            self.__builder._UnsetIterable()

                            return False

                        self.__items.AddLast(value)

                        return True
                    
                    self.__builder._SetIterable(self.__items)
                    
                    return False
                
                def _OnEnded(self) -> None:
                    self.__items = None # type: ignore
                    self.__getEnumerator = None # type: ignore

                    super()._OnEnded()
                
                def _OnStopped(self) -> None:
                    pass
                
                def _ResetOverride(self) -> bool:
                    return True
            
            def __init__(self, builder: IterableBuilder[T], enumerator: IEnumerator[T]):
                super().__init__()

                self.__enumerator: IterableBuilder[T].__Iterable.__Iterable.__Enumerator = IterableBuilder[T].__Iterable.__Iterable.__Enumerator(builder, enumerator)
            
            def TryGetEnumerator(self) -> IEnumerator[T]|None:
                return self.__enumerator.GetItemEnumerator()
        
        def __init__(self, builder: IterableBuilder[T], iterable: IEnumerable[T]):
            super().__init__()

            self.__builder: IterableBuilder[T] = builder
            self.__iterable: IEnumerable[T] = iterable
        
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            enumerator: IEnumerator[T]|None = self.__iterable.TryGetEnumerator()

            if enumerator is None:
                self.__builder._UnsetIterable()

                return None
            
            iterable: IEnumerable[T] = IterableBuilder[T].__Iterable.__Iterable(self.__builder, enumerator)

            self.__builder._SetIterable(iterable)

            return iterable.TryGetEnumerator()
    
    def __init__(self, iterable: IEnumerable[T]):
        super().__init__()

        self.__iterable: IEnumerable[T] = IterableBuilder[T].__Iterable(self, iterable)
    
    @final
    def __SetIterable(self, iterable: IEnumerable[T]) -> None:
        self.__iterable = iterable
    
    @final
    def _SetIterable(self, iterable: IEnumerable[T]) -> None:
        EnsureDirectModuleCall()

        self.__SetIterable(iterable)
    @final
    def _UnsetIterable(self) -> None:
        EnsureDirectModuleCall()

        self.__SetIterable(GetNullEnumerable())
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self.__iterable.TryGetEnumerator()