from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import final

from WinCopies import IDisposable, IInterface
from WinCopies.Typing import IEquatableObject
from WinCopies.Typing.Delegate import Selector
from WinCopies.Typing.Pairing import IKeyValuePair

from WinCopies.Data.Misc import ITableNameFormater

class IColumn(IEquatableObject['IColumn']):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def GetColumnName(self) -> str:
        pass

    def _Equals(self, item: IColumn) -> bool:
        return item.GetColumnName() == self.GetColumnName()
    
    def Equals(self, item: IColumn|object) -> bool:
        return isinstance(item, IColumn) and self._Equals(item)
    
    def Hash(self) -> int:
        return hash(self.GetColumnName())
    
    @abstractmethod
    def ToString(self, selector: Selector[str]) -> str:
        pass
class ITableColumn(IColumn):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetTableName(self) -> str:
        pass
    
    def _Equals(self, item: IColumn) -> bool:
        return isinstance(item, ITableColumn) and item.GetTableName() == self.GetTableName() and super()._Equals(item)
    
    def Equals(self, item: ITableColumn|object) -> bool:
        return isinstance(item, IColumn) and self._Equals(item)
    
    def Hash(self) -> int:
        return hash((self.GetTableName(), self.GetColumnName()))

class Column(IColumn):
    def __init__(self, columnName: str):
        super().__init__()

        self.__columnName: str = columnName
    
    @final
    def GetColumnName(self) -> str:
        return self.__columnName
    
    def ToString(self, selector: Selector[str]) -> str:
        return selector(self.GetColumnName())
class TableColumn(Column, ITableColumn):
    def __init__(self, tableName: str, columnName: str):
        super().__init__(columnName)

        self.__tableName: str = tableName
    
    @final
    def GetTableName(self) -> str:
        return self.__tableName
    
    def ToString(self, selector: Selector[str]) -> str:
        return f"{selector(self.GetTableName())}.{selector(self.GetColumnName())}"

class Operator(Enum):
    Null = 0
    Equals = 1
    IsValue = 2
    IsNot = 3
    Likes = 4
    LessThan = 5
    LessThanOrEquals = 6
    GreaterThan = 7
    GreaterThanOrEquals = 8

    @final
    def __str__(self) -> str:
        match self:
            case Operator.Equals:
                return '='
            
            case Operator.IsValue:
                return "IS"
            
            case Operator.IsNot:
                return "IS NOT"
            
            case Operator.Likes:
                return "LIKE"
            
            case Operator.LessThan:
                return "<"
            case Operator.LessThanOrEquals:
                return "<="
            
            case Operator.GreaterThan:
                return ">"
            case Operator.GreaterThanOrEquals:
                return ">="
            
            case _:
                return ''

class IParameterProvider(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetParameter(self, arg: object|None) -> str:
        """
        Add a given value to the query argument list.

        Parameters:
        - arg: The argument to add to the query argument list.

        Returns:
        A parameter placeholder.
        """
        pass

class IQueryBuilder(ITableNameFormater, IParameterProvider, IDisposable):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def JoinParameters[T](self, items: Iterable[T]) -> str:
        """
        Generates a concatenated string from the arguments retrieved from a given iterable.
        
        The concatenation uses a colon preceding a space as separator.
        
        Each argument is added to the list of query arguments then replaced by a parameter placeholder in the result string.

        Parameters:
        - items: The iterable from which retrieve the arguments.

        Returns:
        The concatenated strings.
        """
        pass
    @abstractmethod
    def JoinOperands(self, items: Iterable[IOperandValue]) -> str:
        pass

class IOperandValue(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Format(self, builder: IQueryBuilder) -> str:
        pass

class __IOperandValue[T](IOperandValue, IKeyValuePair[T, Operator]):
    def __init__(self):
        super().__init__()

class IOperand[T](__IOperandValue[T]):
    def __init__(self):
        super().__init__()

class IColumnOperand(__IOperandValue[IColumn]):
    def __init__(self):
        super().__init__()

class __Operand[T](IInterface):
    def __init__(self, operator: Operator, value: T):
        super().__init__()

        self.__operator: Operator = operator
        self.__value: T = value
    
    @final
    def IsKeyValuePair(self) -> bool:
        return False
    
    @final
    def GetKey(self) -> T:
        return self.__value
    
    @final
    def GetValue(self) -> Operator:
        return self.__operator

class __NullityOperand(IOperand[None]):
    def __init__(self):
        super().__init__()
    
    def IsKeyValuePair(self) -> bool:
        return False
    
    def GetKey(self) -> None:
        return None
    
    def Format(self, builder: IQueryBuilder) -> str:
        return builder.GetParameter(None)

@final
class __NullOperand(__NullityOperand):
    def __init__(self):
        super().__init__()
    
    def GetValue(self) -> Operator:
        return Operator.IsValue
@final
class __NotNullOperand(__NullityOperand):
    def __init__(self):
        super().__init__()
    
    def GetValue(self) -> Operator:
        return Operator.IsNot

__nullOperand: IOperand[None] = __NullOperand()
__notNullOperand: IOperand[None] = __NotNullOperand()

def GetNullOperand() -> IOperand[None]:
    return __nullOperand
def GetNotNullOperand() -> IOperand[None]:
    return __notNullOperand

class Operand[T](__Operand[T], IOperand[T]):
    def __init__(self, operator: Operator, value: T):
        if operator == Operator.Null:
            raise ValueError(f"No operator specified.")
        if value is None:
            raise ValueError("No value given.")

        super().__init__(operator, value)
    
    @final
    def Format(self, builder: IQueryBuilder) -> str:
        return builder.GetParameter(self.GetKey())

class ColumnOperand(__Operand[IColumn], IColumnOperand):
    def __init__(self, operator: Operator, column: IColumn):
        if operator == Operator.Null:
            raise ValueError(f"The operator of a {type(self).__name__} cannot be {Operator.Null.name}")
        
        super().__init__(operator, column)
    
    @final
    def Format(self, builder: IQueryBuilder) -> str:
        return self.GetKey().ToString(builder.FormatTableName)