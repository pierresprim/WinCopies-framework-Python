# -*- coding: utf-8 -*-
"""
Created on Thu May 25 10:04:08 2023

@author: Pierre Sprimont
"""

from abc import ABC, abstractmethod
from typing import final, List #, protected

from WinCopies.Collections import Enumeration

class SequenceGenerator:
    class _Data:
        class _IGenerator(ABC):
            def __init__(self):
                pass
            
            @abstractmethod
            def Render(self, i: int) -> str:
                pass
            
        class _Renderer(_IGenerator):
            def __init__(self, text: str):
                self._text: str = text
            
            #@protected
            @final
            def GetText(self) -> str:
                return self._text
            
        class _TextRenderer(_Renderer):
            def __init__(self, text: str):
                super().__init__(text)
            
            @final
            def Render(self, i: int) -> str:
                return self.GetText()
        
        class _Counter(_IGenerator):
            def __init__(self):
                pass
            
            @final
            def Render(i: int) -> str:
                return str(i)
        
        class _CounterRenderer(_Renderer):
            def __init__(self, text: str):
                super().__init__(text)
            
            @final
            def Render(self, i: int) -> str:
                return self.GetText() + str(i)
            
        class _SequenceGenerator(_IGenerator):
            def __init__(self):
                pass
            
            #@protected
            @abstractmethod
            def GetStr(self, i: int) -> str:
                pass
            #@protected
            @abstractmethod
            def GetExtraStr(self, i: int) -> str:
                pass
            
            @final
            def Render(self, i: int) -> str:
                result: str = ""
                j: int = 0
                
                i -= 1
                
                while j < i:
                    result += self.GetStr(i)
                    j += 1
                
                result += self.GetExtraStr(i)
                
                return result
                
        class _CounterSequenceGenerator(_SequenceGenerator):
            def __init__(self):
                pass
            
            #@protected
            def GetStr(self, i: int) -> str:
                return str(i)
            #@protected
            def GetExtraStr(self, i: int) -> str:
                return str(i)
                        
        class _TextSequenceGenerator(_SequenceGenerator):
            def __init__(self, pattern: str):
                _pattern: List[str] = pattern.split("#", 2)
                
                self._separator: str = _pattern[0]
                self._prefix: str = _pattern[1] if len(_pattern) > 1 else ""
                self._suffix: str = _pattern[2] if len(_pattern) > 2 else ""
            
            #@protected
            def GetExtraStr(self, i: int) -> str:
                return self._prefix + str(i) + self._suffix
            #@protected
            def GetStr(self, i: int) -> str:
                return self.GetExtraStr(i) + self._separator
            
        def __init__(self, pattern: str):
            self._data = ()
            
            def parse() -> None:
                length: int = len(pattern)
                i: int = 0
                start: int = 0
                
                def getSubstr() -> str:
                    return pattern[start : i - start]
                
                while i < length:
                    
                    match pattern[i]:
                        case "\\":
                            if i == length - 1:
                                return
                            
                            i += 2
                            continue
                        
                        case "#":
                            if pattern[i + 1] == "#":
                                if start < i:
                                    self._data += (SequenceGenerator._Data._TextRenderer(getSubstr()),)
                                
                                i += 2
                                start = i
                                
                                while i < length:
                                    if pattern[i] == "#":
                                        i += 1
                                        
                                        if i < length:
                                            if pattern[i] == "#":
                                                substr: str = getSubstr()
                                                self._data += (SequenceGenerator._Data._TextSequenceGenerator(substr) if len(substr) > 0 else SequenceGenerator._Data._CounterSequenceGenerator(),)
                                                
                                                if i == length - 1:
                                                    return
                                                    
                                                break
                                        else:
                                            return
                                                
                                    i += 1
                            
                            else:
                                self._data += (SequenceGenerator._Data._CounterRenderer(getSubstr()) if start < i else SequenceGenerator._Data._Counter(),)
                                
                                if i == length - 1:
                                    return
                                
                            i += 1
                            start = i
                            
                            continue
                                
                    i += 1
        
            parse()
        
        @final
        def Render(self, i: int) -> str:
            result: str = ""
            
            for generator in self._data:
                result += generator.Render(i)
                
            return result
        
    class _Enumerator(Enumeration.Enumerator):
        def __init__(self, sequenceGenerator):
            self._sequenceGenerator: SequenceGenerator = sequenceGenerator
            self._i = 0
            super().__init__()
            
        #@protected
        @final
        def MoveNextOverride(self) -> bool:
            if self._i < self._sequenceGenerator._count:
                self._i += 1
                return True
            
            return False
        #@protected
        @final
        def ResetOverride(self) -> bool:
            self._i = 0
            return True
        @final
        def GetCurrent(self):
            return self._sequenceGenerator._data.Render(self._i)
        @final
        def IsResetSupported(self) -> bool:
            return True
    
    def __init__(self, pattern: str, count: int):
        self._pattern: str = pattern
        self._count: int = count
        self._data: SequenceGenerator._Data = None
        
    @final
    def GetPattern(self) -> str:
        return self._pattern
    
    @final
    def GetCount(self) -> int:
        return self._count
    @final
    def SetCount(self, count: int) -> None:
        self._count = count
    
    @final
    def __iter__(self) -> Enumeration.IEnumerator:
        if self._data == None:
            self._data = SequenceGenerator._Data(self._pattern)
        
        return SequenceGenerator._Enumerator(self)