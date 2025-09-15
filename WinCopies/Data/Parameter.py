from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final

from WinCopies import IInterface

from WinCopies.Collections import Enumeration, Generator
from WinCopies.Collections.Enumeration import IIterable

from WinCopies.Data import IColumn, Column, TableColumn, IOperandValue, IOperand, Operand, GetNullOperand, IColumnOperand, ColumnOperand, Operator, IQueryBuilder

from WinCopies.String import StringifyIfNone

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Delegate import IFunction, ValueFunction
from WinCopies.Typing.Pairing import IKeyValuePair

class IArgument(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Join(self, builder: IQueryBuilder, column: str) -> str:
        pass

class IParameter[T](IIterable[T], IArgument):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Format(self, key: str, values: str|None) -> str:
        pass

class __IColumnParameterGenericConstraint[TKey, TOperand](GenericConstraint[TOperand, IKeyValuePair[TKey, Operator]]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetOperand(self) -> TOperand:
        pass
    
    @final
    def _GetContainer(self) -> TOperand:
        return self.GetOperand()

class __IColumnParameterBase[TKey, TOperand: IOperandValue](IParameter[TOperand], __IColumnParameterGenericConstraint[TKey, TOperand]):
    def __init__(self):
        super().__init__()
class IColumnParameter(__IColumnParameterBase[IColumn, IColumnOperand]):
    def __init__(self):
        super().__init__()
class IFieldParameter[T](__IColumnParameterBase[T, IOperand[T]]):
    def __init__(self):
        super().__init__()

@final
class Parameter(IParameter[None]):
    def __init__(self):
        super().__init__()
    
    def Format(self, key: str, values: str|None) -> str:
        return key
    
    def Join(self, builder: IQueryBuilder, column: str) -> str:
        return self.Format(column, builder.JoinParameters(self))
    
    def TryGetIterator(self) -> None:
        return None

class __ColumnParameterBase[TKey, TOperand: IOperandValue](__IColumnParameterBase[TKey, TOperand]):
    def __init__(self, operand: TOperand):
        super().__init__()

        self.__operand: TOperand = operand
    
    @final
    def GetOperand(self) -> TOperand:
        return self.__operand
    
    @final
    def Join(self, builder: IQueryBuilder, column: str) -> str:
        return self.Format(column, builder.JoinOperands(self))
    
    @final
    def Format(self, key: str, values: str|None) -> str:
        return f"{key} {self._GetInnerContainer().GetValue()} {values}"
    
    @final
    def TryGetIterator(self) -> Generator[TOperand]:
        yield self._GetContainer()
class ColumnParameter(__ColumnParameterBase[IColumn, IColumnOperand], IColumnParameter, IGenericConstraintImplementation[IColumnOperand]):
    def __init__(self, operand: IColumnOperand):
        super().__init__(operand)
    
    @staticmethod
    def Create(operator: Operator, column: IColumn) -> ColumnParameter:
        return ColumnParameter(ColumnOperand(operator, column))
    
    @staticmethod
    def FromColumnName(operator: Operator, columnName: str) -> ColumnParameter:
        return ColumnParameter.Create(operator, Column(columnName))
    @staticmethod
    def CreateForTableColumn(operator: Operator, tableName: str, columnName: str) -> ColumnParameter:
        return ColumnParameter.Create(operator, TableColumn(tableName, columnName))
class FieldParameter[T](__ColumnParameterBase[T, IOperand[T]], IFieldParameter[T], IGenericConstraintImplementation[IOperand[T]]):
    def __init__(self, operand: IOperand[T]):
        super().__init__(operand)
    
    @staticmethod
    def Create(operator: Operator, value: T) -> FieldParameter[T]:
        return FieldParameter[T](Operand(operator, value))

__nullProvider: IFunction[FieldParameter[None]]

class __FunctionUpdater(IFunction["FieldParameter[None]"]):
    def __init__(self):
        super().__init__()
    
    @final
    def GetValue(self) -> FieldParameter[None]:
        __nullProvider = ValueFunction(FieldParameter[None](GetNullOperand()))
        
        return __nullProvider()

__nullProvider = __FunctionUpdater()

@staticmethod
def GetNullFieldParameter() -> FieldParameter[None]:
    return __nullProvider.GetValue()

class RoutineParameter[T](IParameter[T]):
    def __init__(self, args: IIterable[T]):
        super().__init__()

        self.__args: IIterable[T] = args
    
    @final
    def Format(self, key: str, values: str|None) -> str:
        return f"{key}({StringifyIfNone(values)})"
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        return self.__args.TryGetIterator()

class ITableArgument[T](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> T:
        pass
    
    @abstractmethod
    def Render(self, builder: IQueryBuilder) -> str:
        pass
class TableArgument[T](ITableArgument[T]):
    def __init__(self, value: T):
        super().__init__()

        self.__value: T = value
    
    @final
    def GetValue(self) -> T:
        return self.__value

class TableValueArgument[T](TableArgument[T]):
    def __init__(self, value: T):
        super().__init__(value)
    
    @final
    def Render(self, builder: IQueryBuilder) -> str:
        return builder.GetParameter(self.GetValue())
class TableColumnArgument(TableArgument[IColumn]):
    def __init__(self, column: IColumn):
        super().__init__(column)
    
    @final
    def Render(self, builder: IQueryBuilder) -> str:
        return self.GetValue().ToString(builder.FormatTableName)

def MakeTableValueIterable[T](*values: T) -> Iterable[ITableArgument[T]]:
    return (TableValueArgument[T](value) for value in values)
def MakeTableColumnIterable(*columns: IColumn) -> Iterable[ITableArgument[IColumn]]:
    return (TableColumnArgument(column) for column in columns)

class ITableParameter[T](IIterable[ITableArgument[T]]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetAlias(self) -> str|None:
        pass
class TableParameter[T](ITableParameter[T]):
    def __init__(self, alias: str|None, arguments: Iterable[ITableArgument[T]]|None):
        super().__init__()

        self.__alias: str|None = alias
        self.__arguments: IIterable[ITableArgument[T]]|None = Enumeration.Iterable[ITableArgument[T]].TryCreate(arguments)
    
    @final
    def GetAlias(self) -> str|None:
        return self.__alias
    
    @final
    def TryGetIterator(self) -> Iterator[ITableArgument[T]]|None:
        return None if self.__arguments is None else self.__arguments.TryGetIterator()