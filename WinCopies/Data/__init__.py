from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from enum import Enum, Flag, auto
from typing import final

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Collections.Extensions import IReadOnlySet
from WinCopies.Enum import EnsureOneAndOnlyOneFlag, TryGetFieldFromName, TryGetFieldFromValue, TryGetValueFromName
from WinCopies.IO.Stream import IMemoryTextStream, MemoryTextStream
from WinCopies.Typing import ErrorBase, InvalidOperationError
from WinCopies.Typing.Comparison import IHashableValue, HashableProtocol
from WinCopies.Typing.Delegate import Method, Selector
from WinCopies.Typing.Enum import IntEnum, StrEnum
from WinCopies.Typing.Pairing import IKeyValuePair

from WinCopies.Data.Misc import ITableNameFormater

class IColumn(IHashableValue):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetColumnName(self) -> str:
        ...

    def _Equals(self, item: IColumn) -> bool:
        return item.GetColumnName() == self.GetColumnName()
    
    def Equals(self, item: IColumn|object) -> bool: return isinstance(item, IColumn) and self._Equals(item)
    def Hash(self) -> int: return hash(self.GetColumnName())
    
    def ToString(self, selector: Selector[str]) -> str: return selector(self.GetColumnName())
class ITableColumn(IColumn):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetTableName(self) -> str:
        ...
    
    def _Equals(self, item: IColumn) -> bool:
        return isinstance(item, ITableColumn) and item.GetTableName() == self.GetTableName() and super()._Equals(item)
    
    def Equals(self, item: ITableColumn|object) -> bool: return isinstance(item, IColumn) and self._Equals(item)
    def Hash(self) -> int: return hash((self.GetTableName(), self.GetColumnName()))
    
    def ToString(self, selector: Selector[str]) -> str: return f"{selector(self.GetTableName())}.{super().ToString(selector)}"

class Column(Abstract, IColumn):
    def __init__(self, columnName: str) -> None:
        super().__init__()

        self.__columnName: str = columnName
    
    @final
    def GetColumnName(self) -> str: return self.__columnName
class TableColumn(Column, ITableColumn):
    def __init__(self, tableName: str, columnName: str) -> None:
        super().__init__(columnName)

        self.__tableName: str = tableName
    
    @final
    def GetTableName(self) -> str: return self.__tableName

class Operator(Enum):
    Null = 0
    Equals = 1
    IsValue = 2
    IsNot = 3
    IsLike = 4
    IsIn = 5
    LessThan = 6
    LessThanOrEquals = 7
    GreaterThan = 8
    GreaterThanOrEquals = 9

    @final
    def __str__(self) -> str:
        match self:
            case Operator.Equals: return '='
            case Operator.IsLike: return "LIKE"
            
            case Operator.IsValue: return "IS"
            case Operator.IsNot: return "IS NOT"
            
            case Operator.IsIn: return "IN"
            
            case Operator.LessThan: return '<'
            case Operator.LessThanOrEquals: return "<="
            
            case Operator.GreaterThan: return '>'
            case Operator.GreaterThanOrEquals: return ">="
            
            case _: return ''

class ConditionalOperator(Enum):
    Null = 0
    And = 1
    Or = 2

    @final
    def __str__(self) -> str:
        match self:
            case ConditionalOperator.And | ConditionalOperator.Or: return self.name.upper()
            
            case _: return ''
    
    @staticmethod
    def TryParse(value: str) -> ConditionalOperator|None:
        def getValue(*values: ConditionalOperator) -> ConditionalOperator|None:
            for _value in values:
                if value == _value.name.upper(): return _value
            
            return None
        
        return getValue(ConditionalOperator.And, ConditionalOperator.Or)

class OrderingNames(StrEnum):
    Ascending = "ASC"
    Descending = "DESC"
class Ordering(IntEnum):
    Descending = -1
    Null = 0
    Ascending = 1

    @final
    def __str__(self) -> str:
        return TryGetValueFromName(OrderingNames, self.name)
    
    @staticmethod
    def TryParse(value: OrderingNames|str) -> Ordering:
        def getOrdering(ordering: OrderingNames|None) -> Ordering:
            if ordering is None: return Ordering.Null

            result: Ordering|None = TryGetFieldFromName(Ordering, ordering.name)

            return Ordering.Null if result is None else result

        return getOrdering(value if isinstance(value, OrderingNames) else TryGetFieldFromValue(OrderingNames, value))

class IParameterProvider(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetParameter(self, arg: object|None) -> str:
        """
        Add a given value to the query argument list.

        Parameters:
        - arg: The argument to add to the query argument list.

        Returns:
        A parameter placeholder.
        """
        ...

class IQueryBuilder(ITableNameFormater, IParameterProvider, IDisposable):
    def __init__(self) -> None:
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
        ...
    @abstractmethod
    def JoinOperands(self, items: Iterable[IOperandValue]) -> str:
        ...

class IOperandItem[T](IKeyValuePair[T, Operator]):
    def __init__(self) -> None: super().__init__()

class IOperandValue(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Format(self, builder: IQueryBuilder) -> str:
        ...

class IOperand[T](IOperandValue, IOperandItem[T]):
    def __init__(self) -> None: super().__init__()

class ISetOperand[T: HashableProtocol](IOperand[IReadOnlySet[T]]):
    def __init__(self) -> None: super().__init__()

class IColumnOperand(IOperand[IColumn]):
    def __init__(self) -> None: super().__init__()

class _OperandBase[T](Abstract, IOperand[T]):
    def __init__(self, value: T) -> None:
        super().__init__()

        self.__value: T = value
    
    @final
    def IsKeyValuePair(self) -> bool: return False
    
    @final
    def GetKey(self) -> T: return self.__value
class _Operand[T](_OperandBase[T]):
    def __init__(self, operator: Operator, value: T) -> None:
        super().__init__(value)

        self.__operator: Operator = operator
    
    @final
    def GetValue(self) -> Operator: return self.__operator

class _NullityOperand(Abstract, IOperand[None]):
    def __init__(self) -> None: super().__init__()
    
    def IsKeyValuePair(self) -> bool: return False
    
    def GetKey(self) -> None: return None
    
    def Format(self, builder: IQueryBuilder) -> str: return builder.GetParameter(None)

@final
class _NullOperand(_NullityOperand):
    def __init__(self) -> None: super().__init__()
    
    def GetValue(self) -> Operator: return Operator.IsValue
@final
class _NotNullOperand(_NullityOperand):
    def __init__(self) -> None: super().__init__()
    
    def GetValue(self) -> Operator: return Operator.IsNot

__nullOperand: IOperand[None] = _NullOperand()
__notNullOperand: IOperand[None] = _NotNullOperand()

def GetNullOperand() -> IOperand[None]:
    return __nullOperand
def GetNotNullOperand() -> IOperand[None]:
    return __notNullOperand

class Operand[T](_Operand[T]):
    def __init__(self, operator: Operator, value: T) -> None:
        if operator == Operator.Null: raise ValueError("No operator specified.")
        if value is None: raise ValueError("No value given.")

        super().__init__(operator, value)
    
    @final
    def Format(self, builder: IQueryBuilder) -> str: return builder.GetParameter(self.GetKey())

class SetOperand[T: HashableProtocol](_OperandBase[IReadOnlySet[T]], ISetOperand[T]):
    def __init__(self, value: IReadOnlySet[T]) -> None: super().__init__(value)
    
    @final
    def GetValue(self) -> Operator: return Operator.IsIn
    
    @final
    def Format(self, builder: IQueryBuilder) -> str:
        action: Method[T]|None = None

        def _process(arg: T) -> None: builder.GetParameter(arg)
        
        def process(arg: T) -> None:
            def process(arg: T) -> None:
                result.Write(',')
                
                _process(arg)

            nonlocal action

            _process(arg)

            action = process

        args: IReadOnlySet[T] = self.GetKey()
        result: IMemoryTextStream = MemoryTextStream()

        result.Write('(')

        action = process

        for arg in args.AsIterable(): action(arg)

        result.Write(')')

        return result.ToString()

class ColumnOperand(_Operand[IColumn], IColumnOperand):
    def __init__(self, operator: Operator, column: IColumn) -> None:
        if operator == Operator.Null: raise ValueError(f"The operator of a {type(self).__name__} cannot be {Operator.Null.name}")
        
        super().__init__(operator, column)
    
    @final
    def Format(self, builder: IQueryBuilder) -> str: return self.GetKey().ToString(builder.FormatTableName)

class QueryErrorKinds(Flag):
    Null = 0
    ParameterLimitExceeded = auto()
    QuerySizeExceeded = auto()
    ConnectionLost = auto()

    def __str__(self) -> str:
        match self:
            case QueryErrorKinds.Null: return "No error."
            
            case QueryErrorKinds.ParameterLimitExceeded: return "The query parameter count exceeds this DBMS's capacity."
            case QueryErrorKinds.QuerySizeExceeded: return "The query size exceeds this DBMS's capacity."
            case QueryErrorKinds.ConnectionLost: return "The connection is no longer active."
            
            case _: return "Invalid error value."

class QueryError(ErrorBase):
    def __init__(self, errorKind: QueryErrorKinds, *args: object) -> None:
        EnsureOneAndOnlyOneFlag(errorKind)

        super().__init__(errorKind, *args)

        self.__errorKind: QueryErrorKinds = errorKind
    
    @final
    def GetMessage(self) -> str: return str(self.__errorKind)
    
    @final
    def GetErrorKind(self) -> QueryErrorKinds: return self.__errorKind

def GetActiveTransactionError() -> Exception: return InvalidOperationError("A transaction is already active on this connection.")