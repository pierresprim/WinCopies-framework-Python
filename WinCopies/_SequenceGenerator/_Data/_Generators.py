from abc import ABC, abstractmethod
from typing import final #, protected
from enum import Enum

from WinCopies.Typing import singleton

class _IGenerator(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def Render(self, i: int) -> str:
        pass

class _Renderer(_IGenerator):
    def __init__(self, textProvider: callable):
        self.__textProvider: callable = textProvider
    
    #@protected
    @final
    def GetText(self) -> str:
        return self.__textProvider()
    
    def __eq__(self, other) -> bool:
        return isinstance(other, _Renderer) and self.__textProvider == other.__textProvider

class _TextRenderer(_Renderer):
    def __init__(self, textProvider: callable):
        super().__init__(textProvider)
    
    @final
    def Render(self, i: int) -> str:
        return self.GetText()

class _ICounter(ABC):
    def __init__(self, before: bool):
        self.__before: bool = before
    
    @final
    def _Init(self, isVariable: bool|None, updater: callable) -> None:
        def init(isVariable: bool, before: bool) -> None:
            _ICounter.__init__(self, before)
            updater(isVariable)
        
        if isVariable is None:
            init(True, True)
        elif isVariable is True:
            init(True, False)
        else:
            updater(False)
    
    def ToBool(isVariable: bool|None) -> bool:
        return isVariable is None
    
    def ToNullableBool(before: bool) -> bool|None:
        return None if before else True
    
    @abstractmethod
    def IsVariableSpace(self) -> bool:
        pass
    
    @abstractmethod
    def Render(self, i: int) -> str:
        pass
    
    @final
    def _RenderSpace(self, i: int, spaceCount: int) -> str:
        def render() -> str:
            return self.Render(i)
        
        space: str = " " * spaceCount
        
        return space + render() if self.__before else render() + space
    
    def RenderSpace(self, i: int, spaceCount: int, nextLevel: bool, step: int|None) -> str:
        return self._RenderSpace(i, spaceCount)
    
    @final
    def Equals(self, other) -> bool:
        return other.__before == self.__before
    
    def __eq__(self, other) -> bool:
        return isinstance(other, _ICounter) and self.Equals(other)

@final
class _Counter(_IGenerator, _ICounter):
    def __init__(self, isVariable: bool|None):
        self.__isVariable: bool

        def update(isVariable: bool) -> None:
            self.__isVariable = isVariable

        self._Init(isVariable, update)
    
    def GetVariableSpaceInitializer(before: bool):
        return lambda: _Counter(_ICounter.ToNullableBool(before))
    def GetFixedSpace():
        return _Counter(False)
    
    def IsVariableSpace(self) -> bool:
        return self.__isVariable
    
    def Render(self, i: int) -> str:
        return str(i)
    
    def __eq__(self, other) -> bool:
        return isinstance(other, _Counter) and other.IsVariableSpace() and super().Equals(other)

@final
class _CounterRenderer(_Renderer, _ICounter):
    def __init__(self, textProvider: callable, isVariable: bool|None):
        self.__isVariable: bool

        def update(isVariable: bool) -> None:
            self.__isVariable = isVariable

        self._Init(isVariable, update)
        super().__init__(textProvider)
    
    def GetVariableSpaceInitializer(before: bool):
        return lambda textProvider: _CounterRenderer(textProvider, _ICounter.ToNullableBool(before))
    def GetFixedSpace(textProvider: callable):
        return _CounterRenderer(textProvider, False)
    
    def IsVariableSpace(self) -> bool:
        return self.__isVariable
    
    def Render(self, i: int) -> str:
        return self.GetText() + str(i)

    def __eq__(self, other) -> bool:
        return isinstance(other, _CounterRenderer) and other.IsVariableSpace() and super().__eq__(other) and super().Equals(other)

class _Operator(_IGenerator):
    class _Operator:
        class _Operator(Enum):
            """Identifies an operator."""
            Add = 1
            """The addition operator."""
            Sub = 2
            """The subtraction operator."""
            Mul = 3
            """The multiplication operator."""
            Div = 4
            """The division operator."""
            Mod = 5
            """The modulus operator."""
            Pow = 6
            """The power operator."""
            Fac = 7
            """The factorial operator."""
            Spw = 8
            """The super power operator."""
        
        def __init__(self, operator: callable, operatorId: _Operator):
            self.__operator: callable = operator
            self.__operatorId: _Operator = operatorId
        
        def __call__(self, i: int) -> int:
            return self.__operator(i)
        
        def __eq__(self, other) -> bool:
            return isinstance(other, _Operator) and other.__operatorId == self.__operatorId
        
        @final
        def GetOperatorId(self) -> _Operator:
            return self.__operatorId
        
    def __init__(self, operator: callable, operatorId: _Operator._Operator):
        self.__operator: _Operator._Operator = _Operator._Operator(operator, operatorId)
    
    def GetInitializer(operator: callable, operatorId: _Operator._Operator) -> callable:
        return lambda: _Operator(operator, operatorId)
    
    def GetInitializerStr(operator: str, isVariable: bool|None) -> callable:
        def _getInitializer(operator: callable, operatorId: _Operator._Operator) -> callable:
            return lambda: _VariableSpaceOperator(operator, operatorId, _ICounter.ToBool(isVariable)) if isVariable else _Operator(operator, operatorId)
        
        def getInitializer(operator: callable, operatorId: _Operator._Operator) -> callable:
            return _Operator.GetInitializer(operator, operatorId)
        
        match operator:
            case '+':
                return _getInitializer(lambda value: value + 1, _Operator._Operator._Operator.Add)
            case '-':
                return _getInitializer(lambda value: value - 1, _Operator._Operator._Operator.Sub)
            case '*':
                return getInitializer(lambda value: value * 2, _Operator._Operator._Operator.Mul)
            case '/':
                return getInitializer(lambda value: value / 2, _Operator._Operator._Operator.Div)
            case '%':
                return getInitializer(lambda value: value % 2, _Operator._Operator._Operator.Mod)
            case '^':
                return getInitializer(lambda value: value ^ 2, _Operator._Operator._Operator.Pow)
    
    @final
    def GetOperatorId(self) -> _Operator._Operator:
        return self.__operator.GetOperatorId()
    
    @final
    def _GetSpaceCountProvider(operatorId: _Operator._Operator) -> callable:
        return (lambda spaceCount, nextLevel, step: (spaceCount - 1 if step == 1 else spaceCount)) if operatorId == _Operator._Operator._Operator.Add else (lambda spaceCount, nextLevel, step: (spaceCount + 1 if nextLevel else spaceCount))
    
    def Render(self, i: int) -> str:
        return str(self.__operator(i))
    
    def __eq__(self, other) -> bool:
        return isinstance(other, _Operator) and other.__operator == self.__operator

@final
class _OperatorRenderer(_Renderer):
    def __init__(self, textProvider: callable, operator: callable):
        super().__init__(textProvider)
        self.__operator: callable = operator
    
    def GetInitializer(operator: callable, operatorId: _Operator._Operator._Operator) -> callable:
        return lambda text: _OperatorRenderer(text, _Operator._Operator(operator, operatorId))
    
    def Render(self, i: int) -> str:
        return self.GetText() + str(self.__operator(i))

    def __eq__(self, other) -> bool:
        return isinstance(other, _OperatorRenderer) and other.__operator == self.__operator and super().__eq__(other)

class _OperatorParser(_IGenerator):
    def __init__(self, operand: int, operator: callable, operatorId: _Operator._Operator._Operator):
        self.__operand: int = operand
        self.__operator: callable = _Operator._Operator(lambda value: operator(value, operand), operatorId)
    
    def GetInitializer(operator: str, isVariable: bool|None) -> callable:
        def getConstructor(parserInitializer: callable, operatorInitializer: callable, compareWith: int, operator: callable, operatorId: _Operator._Operator._Operator) -> callable:
            def getConstructor(text: str) -> callable:
                value: int = int(text)
                
                return parserInitializer(value, operator, operatorId) if value == compareWith else operatorInitializer(operator, operatorId)
            
            return getConstructor
        
        def _getInitializer(operator: callable, operatorId: _Operator._Operator._Operator) -> callable:
            if isVariable is False:
                parserInitializer: callable = _OperatorParser
                operatorInitializer: callable = _Operator
            else:
                before: bool = _ICounter.ToBool(isVariable)

                parserInitializer: callable = lambda operand, operator, operatorId: _VariableSpaceOperatorParser(operand, operator, operatorId, before)
                operatorInitializer: callable = lambda operator, operatorId: _VariableSpaceOperator(operator, operatorId, before)
                
            return getConstructor(parserInitializer, operatorInitializer, 1, operator, operatorId)
        
        def getInitializer(operator: callable, operatorId: _Operator._Operator._Operator) -> callable:
            return getConstructor(_OperatorParser, _Operator, 2, operator, operatorId)
        
        match operator:
            case '+':
                return _getInitializer(lambda x, y: x + y, _Operator._Operator._Operator.Add)
            case '-':
                return _getInitializer(lambda x, y: x - y, _Operator._Operator._Operator.Sub)
            case '*':
                return getInitializer(lambda x, y: x * y, _Operator._Operator._Operator.Mul)
            case '/':
                return getInitializer(lambda x, y: x / y, _Operator._Operator._Operator.Div)
            case '%':
                return getInitializer(lambda x, y: x % y, _Operator._Operator._Operator.Mod)
            case '^':
                return getInitializer(lambda x, y: x ^ y, _Operator._Operator._Operator.Pow)
    
    @final
    def Render(self, i: int) -> str:
        return str(self.__operator(i))

    def __eq__(self, other) -> bool:
        return isinstance(other, _OperatorParser) and other.__operand == self.__operand and other.__operator == self.__operator

@final
class _VariableSpaceOperator(_Operator, _ICounter):
    def __init__(self, operator: callable, operatorId: _Operator._Operator._Operator, before: bool):
        super().__init__(operator, operatorId)
        _ICounter.__init__(self, before)

        self.__getSpaceCount = _Operator._GetSpaceCountProvider(self.GetOperatorId())
    
    def IsVariableSpace(self) -> bool:
        return True
    
    def RenderSpace(self, i: int, spaceCount: int, nextLevel: bool, step: int|None) -> str:
        return self._RenderSpace(i, self.__getSpaceCount(spaceCount, nextLevel, step))
    
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and _ICounter.__eq__(self, other)

@final
class _VariableSpaceOperatorParser(_OperatorParser, _ICounter):
    def __init__(self, operand: int, operator: callable, operatorId: _Operator._Operator._Operator, before: bool):
        super().__init__(operand, operator, operatorId)
        _ICounter.__init__(before)
        
        self.__getSpaceCount: callable = None
        
        if operand == 1:
            self.__getSpaceCount = _Operator._GetSpaceCountProvider(operatorId)
        
        else:
            _spaceCount: int = 0

            if operatorId == _Operator._Operator._Operator.Add:
                _operator: callable = lambda spaceCount: spaceCount - 1
                condition: callable = lambda nextLevel, step: step == operand
            
            else:
                _operator: callable = lambda spaceCount: spaceCount + 1
                condition: callable = lambda nextLevel, step: nextLevel
            
            def getSpaceCount(spaceCount: int, nextLevel: bool, step: int|None) -> int:
                nonlocal _spaceCount

                def getSpaceCount() -> int:
                    return _operator(spaceCount)

                if condition(nextLevel, spaceCount):
                    _spaceCount = operand
                    
                    return getSpaceCount()
                
                if _spaceCount > 0:
                    _spaceCount -= 1                
                    
                    return getSpaceCount()
                
                return spaceCount
            
            self.__getSpaceCount = getSpaceCount
    
    @final
    def IsVariableSpace(self) -> bool:
        return True
    
    @final
    def RenderSpace(self, i: int, spaceCount: int, nextLevel: bool, step: int|None) -> str:
        return self.Render(i) + " " * self.__getSpaceCount(spaceCount, nextLevel, step)
    
    def __eq__(self, other) -> bool:
        return super().__eq__(self, other) and _ICounter.__eq__(self, other)

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
            j += 1
            result += self.GetStr(j)
        
        result += self.GetExtraStr(j + 1)
        
        return result

@singleton
@final
class _CounterSequenceGenerator(_SequenceGenerator):
    def __init__(self):
        pass
    
    #@protected
    def GetStr(self, i: int) -> str:
        return str(i)
    #@protected
    def GetExtraStr(self, i: int) -> str:
        return str(i)
    
    def __eq__(self, other) -> bool:
        return isinstance(other, _CounterSequenceGenerator)

@final
class _TextSequenceGenerator(_SequenceGenerator):
    def __init__(self, pattern):
        self.__pattern = pattern
    
    #@protected
    def GetExtraStr(self, i: int) -> str:
        return self.__pattern._GetPrefix() + str(i) + self.__pattern._GetSuffix()
    #@protected
    def GetStr(self, i: int) -> str:
        return self.GetExtraStr(i) + self.__pattern._GetSeparator()
    
    def __eq__(self, other) -> bool:
        return isinstance(other, _TextSequenceGenerator) and other.__pattern == self.__pattern