from typing import final #, protected
from math import pow, factorial, log10

from ._Generators import _IGenerator, _TextRenderer, _ICounter, _Counter, _CounterRenderer, _TextSequenceGenerator, _CounterSequenceGenerator, _Operator, _OperatorRenderer, _OperatorParser
from WinCopies.Collections.Linked.Singly import Queue
from WinCopies.Collections import Enumeration, ForEachUntilValue, GetLastIndex, TrySetAt, DoWhile
from WinCopies import Replace

@final
class _Data:
    @final
    class _Generators:
        @final
        class _Enumerator(Enumeration.Enumerator):
            def __init__(self, generators):
                self.__generators = generators
                self.__i: int

                self.__Reset()
                
                super().__init__()
            
            #@protected
            def MoveNextOverride(self) -> bool:
                self.__i += 1
                
                return self.__i < self.__generators._GetLength()
                                    
            def IsResetSupported(self) -> bool:
                return True
            def __Reset(self) -> None:
                self.__i = -1
            #@protected
            def ResetOverride(self) -> bool:
                self.__Reset()
                return True
            
            def GetCurrent(self):
                return self.__generators._GetAt(self.__i)
        
        class _Strings:
            """Contains all the strings used by SequenceGenerator. This class ensures that each string is stored uniquely, even when referenced by multiple generators."""

            class _TextProvider:
                def __init__(self, string: str):
                    self.__string: str = string
                
                def __call__(self) -> str:
                    return self.__string
                
                def __eq__(self, other) -> bool:
                    def eq(t: type, func: callable) -> bool:
                        return isinstance(other, t) and func() == self.__string

                    return eq(str, lambda: other) or eq(_Data._Generators._Strings._TextProvider, lambda: other.__string)
            
            class _TextSequenceProvider:
                def __init__(self, pattern: str, strings):
                    def getEmpty() -> callable:
                        return lambda: ""

                    _pattern: list[str] = pattern.split("#", 2)
                    
                    def add(index: int) -> callable:
                        return strings._Add(_pattern[index])
                    def tryGetAt(index: int) -> callable:
                        return TrySetAt(_pattern, index, add, getEmpty)

                    self.__separator: callable = add(0)
                    self.__prefix: callable = tryGetAt(1)
                    self.__suffix: callable = tryGetAt(2)

                def _GetSeparator(self) -> str:
                    return self.__separator()
                def _GetPrefix(self) -> str:
                    return self.__prefix()
                def _GetSuffix(self) -> str:
                    return self.__suffix()
                
                def __eq__(self, other) -> bool:
                    return isinstance(other, _Data._Generators._Strings._TextSequenceProvider) and other.__separator == self.__separator and other.__prefix == self.__prefix and other.__suffix == self.__suffix
            
            def __init__(self):
                self.__list = []
                """Contains the strings stored by this class."""
            
            def _Add(self, newString: str) -> callable:
                func: _Data._Generators._Strings._TextProvider = None

                newString = Replace(newString, '\\', '', '#', '~', '@', ':', '!', '+', '-', '*', '/', '%', '^')

                def getFunc(index: int) -> callable:
                    return self.__list[index]
                
                def add(index: int, string: str) -> None:
                    nonlocal func

                    func = getFunc(index)

                if ForEachUntilValue(self.__list, add, newString):
                    return func
                
                self.__list.append(_Data._Generators._Strings._TextProvider(newString))

                return getFunc(GetLastIndex(self.__list))
            
            def _GetPattern(self, pattern: str) -> _TextSequenceProvider:
                return _Data._Generators._Strings._TextSequenceProvider(pattern, self)
        
        def __init__(self):
            self.__list = []
            self.__tuple = ()

            self.__strings: _Data._Generators._Strings = _Data._Generators._Strings()
        
        def _Add(self, newGenerator: _IGenerator) -> None:
            def add(index: int, generator: _IGenerator = None) -> None:
                self.__tuple += (index, )
            
            if ForEachUntilValue(self.__list, add, newGenerator):
                return
            
            self.__list.append(newGenerator)

            add(GetLastIndex(self.__list))
        
        def _GetAt(self, index: int) -> _IGenerator:
            return self.__list[self.__tuple[index]]
        
        def _GetLength(self) -> int:
            return len(self.__tuple)

        def _AddString(self, string: str) -> callable:
            return self.__strings._Add(string)

        def _GetPattern(self, pattern: str) -> _Strings._TextSequenceProvider:
            return self.__strings._GetPattern(pattern)

        def __iter__(self) -> Enumeration.IEnumerator:
            return _Data._Generators._Enumerator(self)

    def __init__(self, pattern: str):
        self.__data: _Data._Generators = _Data._Generators()
        
        def parse() -> None:                    
            length: int = len(pattern)
            i: int = 0
            start: int = 0
            tuples: tuple = (('#', None), ('~', False), ('@', True))
            
            def getSubstrProvider() -> callable:
                return self.__data._AddString(pattern[start : i])
            def hasText() -> bool:
                return start < i
            
            def _increment(step: int) -> None:
                nonlocal i
                nonlocal start

                i += step
                start = i

            def increment() -> None:
                _increment(1)
            
            def append(textGenerator: _IGenerator) -> None:
                self.__data._Add(textGenerator)
            def appendTextGenerator() -> None:
                append(_TextRenderer(getSubstrProvider()))
            def appendSequence(ifTrue: callable, ifFalse: callable) -> None:
                append(ifTrue(getSubstrProvider()) if hasText() else ifFalse())
            def appendOperator(operator: callable, isFactorial: bool) -> None:
                nonlocal i
                nonlocal start

                operatorId: _Operator._Operator._Operator = _Operator._Operator._Operator.Fac if isFactorial else _Operator._Operator._Operator.Spw

                appendSequence(_OperatorRenderer.GetInitializer(operator, operatorId), _Operator.GetInitializer(operator, operatorId))
                
                increment()
            
            def tryAppend() -> None:
                if start < i:
                    appendTextGenerator()
            def eol() -> bool:
                return i == length - 1
            
            def onVariableSpace(before: bool) -> bool:
                appendSequence(_CounterRenderer.GetVariableSpaceInitializer(before), _Counter.GetVariableSpaceInitializer(before),)
                        
                if eol():
                    return False
                
                increment()
                
                return True
                        
            while i < length:
                match pattern[i]:
                    case '\\':
                        if eol():
                            break
                        
                        i += 2
                        
                        continue
                    
                    case '~':
                        if onVariableSpace(False):
                            continue

                        return

                    case '@':
                        if onVariableSpace(True):
                            continue

                        return
                    
                    case '#':
                        def __appendSequence() -> None:
                            appendSequence(_CounterRenderer.GetFixedSpace, _Counter.GetFixedSpace)
                        
                        if eol():
                            __appendSequence()
                            
                            return
                        
                        if pattern[i + 1] == '#':
                            def _appendSequence() -> None:
                                append(_TextSequenceGenerator(self.__data._GetPattern(getSubstrProvider())) if hasText()  else _CounterSequenceGenerator())
                            
                            tryAppend()
                            
                            _increment(2)
                            
                            while i < length:
                                if pattern[i] == '#':
                                    i += 1
                                    
                                    if i < length:
                                        if pattern[i] == '#':
                                            if eol():
                                                _appendSequence()
                                                
                                                return
                                                
                                            break
                                    else:
                                        _appendSequence()
                                        
                                        return
                                            
                                i += 1
                            
                            _appendSequence()
                        
                        else:
                            __appendSequence()
                            
                        increment()
                        
                        continue
                    
                    case '!':
                        appendOperator(factorial, True)
                        
                        continue
                    
                    case ':':
                        appendOperator(lambda value: value ^ value, False)
                        
                        continue
                    
                current: str = pattern[i]
                
                def ___appendSequence(isVariable: bool|None) -> None:
                    appendSequence(_OperatorParser.GetInitializer(current, isVariable), _Operator.GetInitializerStr(current, isVariable))
                
                def _appendSequence() -> None:
                    ___appendSequence(False)
                
                def ____appendSequence(before: None) -> None:
                    _appendSequence()
                
                def checkOperator() -> object|None:
                    def checkOperator(*operators: str) -> bool:
                        for operator in operators:
                            if operator == current:
                                return True
                        
                        return False
                    
                    if checkOperator('+', '-'):
                        return lambda before: ___appendSequence(_ICounter.ToNullableBool(before))
                    
                    if checkOperator('*', '/', '%', '^'):
                        return ____appendSequence
                    
                    return None
                
                action: callable|None = checkOperator()
                
                if action is None:
                    i += 1
                    
                    continue
                
                tryAppend()
                increment()
                
                def check() -> bool|None:
                    nonlocal i
                    
                    def check() -> bool|None:
                        def check(char: str, action: callable, before: bool|None) -> bool|None:
                            if pattern[i] == char:
                                if eol():
                                    action(before)
                                    
                                    return None
                                
                                action(before)
                                
                                return False
                            
                            return True
                        
                        result: bool|None
                        tuple: tuple[str, bool|None]
                        j: int = 0
                        getAction: callable
                        
                        def _action() -> None:
                            nonlocal result

                            tuple = tuples[j]

                            result = check(tuple[0], getAction(), tuple[1])

                        def _getAction() -> callable:
                            nonlocal getAction
                            
                            getAction = lambda: action

                            return ____appendSequence
                        
                        getAction = _getAction
                        
                        def onLoop() -> bool:
                            nonlocal j

                            if result is True:
                                j += 1
                                
                                return j <= 2
                            
                            return False
                        
                        DoWhile(_action, onLoop)
                        
                        return result
                    
                    result: bool|None
                    
                    while i < length:
                        result = check()
                        
                        if result is True:
                            i += 1
                            continue
                        
                        return result
                    
                    return True
                
                match check():
                    case False:
                        increment()
                        
                        continue
            
                    case True:
                        _appendSequence()
                
                return
            
            if start < i:
                appendTextGenerator()

        parse()
        
    def RenderFirst(self, i: int, count: int) -> tuple[str, callable]:
        result: str = ""
        renderer: callable = None
        identical: bool|None = True
        _i: int
        nextLevel: bool
        step: int|None
        
        def isVariableSpace(generator: _IGenerator) -> bool:
            return isinstance(generator, _ICounter) and generator.IsVariableSpace()
        
        def render(generator: _IGenerator, variableSpace: bool|None = None) -> None:
            nonlocal result
            
            result += generator.RenderSpace(i, count, nextLevel, step) if (variableSpace if type(variableSpace) is bool else isVariableSpace(generator)) else generator.Render(i)
        
        def renderFirst(generator: _IGenerator) -> None:
            nonlocal renderer
            nonlocal identical
            
            if isVariableSpace(generator):
                render(generator, True)
            else:
                identical = False
                render(generator, identical)
            
            def renderNextItems(generator: _IGenerator) -> None:
                nonlocal renderer
                nonlocal identical
                
                def _render() -> None:
                    render(generator, identical)
                
                if isVariableSpace(generator) == identical:
                    _render()
                
                else:
                    identical = None
                    _render()
                    renderer = render
            
            renderer = renderNextItems
        
        def isNextLevel(i: int) -> tuple[bool, int|None]:
            nonlocal count
            nonlocal _i

            if i == _i:
                _i *= 10
                count -= 1

                return (True, None)
            
            return (False, _i - i)
        
        def setCount() -> None:
            nonlocal count
            nonlocal _i

            __i: int = int(log10(i))

            _i = int(pow(10, __i + 1))
            count = int(log10(count)) - __i
        
        setCount()
        
        (nextLevel, step) = isNextLevel(i)
        renderer = renderFirst
        
        for generator in self.__data:
            renderer(generator)
        
        def getRenderer() -> callable:
            if identical is False:
                def _render(i: int) -> str:
                    result = ""
                    
                    for generator in self.__data:
                        result += generator.Render(i)
                    
                    return result
                
                return _render
                
            def getRenderer(func: callable) -> callable:
                def _render(i: int) -> str:
                    nonlocal _i
                    nonlocal count
                    
                    def render(tuple: tuple[bool, int|None]) -> str:
                        return func(i, count, tuple)
                    
                    return render(isNextLevel(i))
                
                return _render
            
            def getFunc(func: callable) -> callable:
                def _func(i: int, count: int, tuple: tuple[bool, int|None]) -> str:
                    result = ""
                        
                    for generator in self.__data:
                        result += func(generator, i, count, tuple[0], tuple[1])
                        
                    return result
                
                return _func
            
            return getRenderer(getFunc(lambda generator, i, count, nextLevel, step: generator.RenderSpace(i, count, nextLevel, step))) if identical is True else getRenderer(getFunc(lambda generator, i, count, nextLevel, step: generator.RenderSpace(i, count, nextLevel, step) if isVariableSpace(generator) else generator.Render(i)))
        
        return (result, getRenderer())