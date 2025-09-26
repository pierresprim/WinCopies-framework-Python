from __future__ import annotations


from abc import abstractmethod
from collections.abc import Iterable
from typing import final, Callable, Self



from WinCopies import IInterface

from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction.Enumeration import CountableEnumerable
from WinCopies.Collections.Enumeration import ICountableEnumerable
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Singly import ICountableIterableList, CountableIterableQueue

from WinCopies.IO.Stream import IMemoryTextStream, MemoryTextStream

from WinCopies.Typing.Delegate import Converter, Method
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult



from WinCopies.Data import IOperandValue, IColumn, IQueryBuilder
from WinCopies.Data.Misc import JoinType, IQueryBase
from WinCopies.Data.Parameter import IArgument
from WinCopies.Data.Set import ITableParameter

class IConditionalQueryWriter(IQueryBuilder):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def OpenStream(self) -> None:
        pass

    @abstractmethod
    def Write(self, value: str) -> None:
        pass
    
    @abstractmethod
    def AddConditions(self, conditions: IParameterSetBase[IConditionalQueryWriter]|None) -> None:
        pass
    
    @abstractmethod
    def ProcessConditions[T: IArgument|None](self, items: IDictionary[IColumn, T]) -> Generator[str]:
        pass

class IConditionalQueryBuilder(IConditionalQueryWriter):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def Build(self) -> DualResult[str, ICountableEnumerable[object]|None]:
        pass

class ISelectionQueryWriter(IConditionalQueryWriter):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def AddTable(self, name: str, parameter: ITableParameter[object]|None) -> str:
        """
        SQL-formats a given table or routine call.

        Parameters:
        - name: A name of either a table or routine call.
        - parameter: The arguments of the routine call, if applicable.

        Returns:
        The SQL formatted result of the table or routine call parsing.
        """
        pass

    @abstractmethod
    def AddJoins(self, joins: Iterable[IJoinBase[IParameterSetBase[ISelectionQueryWriter]]]|None) -> None:
        pass
    
    @abstractmethod
    def ProcessCondition(self, condition: IKeyValuePair[IColumn, IArgument|None]) -> str:
        pass

class ISelectionQueryBuilder(IConditionalQueryBuilder, ISelectionQueryWriter):
    def __init__(self):
        super().__init__()

class IParameterSetBase[T: IConditionalQueryWriter](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Render(self, writer: T) -> None:
        pass

class IJoinBase[T: IParameterSetBase[ISelectionQueryWriter]](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetType(self) -> JoinType:
        pass

    @abstractmethod
    def GetTableName(self) -> str:
        pass

    @abstractmethod
    def GetTableParameter(self) -> ITableParameter[object]:
        pass
    
    @abstractmethod
    def GetConditions(self) -> T|None:
        pass

class __ConditionalQueryWriter[T: IConditionalQueryWriter](IConditionalQueryWriter):
    def __init__(self, prefix: str, writer: T):
        def write(value: str) -> None:
            def write(value: str) -> None:
                self.__builder.Write(value)
            
            write(prefix + value)
            
            self.__write = write
        
        super().__init__()
        
        self.__builder: T = writer
        self.__write: Method[str] = write
    
    @final
    def _GetBuilder(self) -> T:
        return self.__builder
    
    def FormatTableName(self, name: str) -> str:
        return self._GetBuilder().FormatTableName(name)
    
    def OpenStream(self) -> None:
        self._GetBuilder().OpenStream()

    def Write(self, value: str) -> None:
        return self.__write(value)

    def JoinParameters[TItems](self, items: Iterable[TItems]) -> str:
        return self._GetBuilder().JoinParameters(items)
    def JoinOperands(self, items: Iterable[IOperandValue]) -> str:
        return self._GetBuilder().JoinOperands(items)
    
    def AddConditions(self, conditions: IParameterSetBase[IConditionalQueryWriter]|None) -> None:
        return self._GetBuilder().AddConditions(conditions)
    
    def ProcessConditions(self, items: IDictionary[IColumn, IArgument|None]) -> Generator[str]:
        return self._GetBuilder().ProcessConditions(items)
@final
class __SelectionQueryWriter(__ConditionalQueryWriter[ISelectionQueryWriter], ISelectionQueryWriter):
    def __init__(self, prefix: str, writer: ISelectionQueryWriter):
        super().__init__(prefix, writer)

    def AddTable(self, name: str, parameter: ITableParameter[object]|None) -> str:
        return self._GetBuilder().AddTable(name, parameter)

    def AddJoins(self, joins: Iterable[IJoinBase[IParameterSetBase[ISelectionQueryWriter]]]|None) -> None:
        return self._GetBuilder().AddJoins(joins)
    
    def ProcessCondition(self, condition: IKeyValuePair[IColumn, IArgument|None]) -> str:
        return self._GetBuilder().ProcessCondition(condition)

def GetPrefixedConditionalQueryWriter(prefix: str, writer: IConditionalQueryWriter) -> IConditionalQueryWriter:
    return __ConditionalQueryWriter(prefix, writer)
def GetPrefixedSelectionQueryWriter(prefix: str, writer: ISelectionQueryWriter) -> ISelectionQueryWriter:
    return __SelectionQueryWriter(prefix, writer)

class ConditionalQueryBuilder(IConditionalQueryBuilder):
    def __init__(self, query: IQueryBase[object]):
        super().__init__()

        self.__query: IQueryBase[object] = query
        self.__stream: IMemoryTextStream = MemoryTextStream()
        self.__args: ICountableIterableList[object] = CountableIterableQueue[object]()
    
    @final
    def _GetQuery(self) -> IQueryBase[object]:
        return self.__query
    
    @final
    def _GetStream(self) -> IMemoryTextStream:
        return self.__stream
    
    @final
    def _GetArgs(self) -> ICountableIterableList[object]:
        return self.__args
    
    @final
    def _RenderConditions[T: IConditionalQueryWriter](self, prefix: str, conditions: IParameterSetBase[T]|None, func: Callable[[str, Self], T]) -> None:
        if conditions is None:
            return
        
        conditions.Render(func(prefix, self))
    
    @final
    def OpenStream(self) -> None:
        self.__stream.Open()
    
    @final
    def Write(self, value: str) -> None:
        self.__stream.Write(value)
    
    @final
    def FormatTableName(self, name: str) -> str:
        return self._GetQuery().FormatTableName(name)

    @final
    def __Push(self, arg: object) -> None:
        """
        Add a given value to the list of query arguments.

        Parameters:
        - arg: The argument to add.
        """
        self._GetArgs().Push(arg)
    
    @final
    def GetParameter(self, arg: object|None) -> str:
        if arg is None:
            return "NULL"
        
        self.__Push(arg)
        
        return '?'
    
    @staticmethod
    def Join(values: Iterable[str]) -> str:
        """
        Concatenates the strings retrieved from a given iterable using a colon preceding a space as separator.

        Parameters:
        - values: The iterable from which retrieve the strings to concatenate.

        Returns:
        The concatenated strings.
        """
        return ', '.join(values)
    
    @final
    def _JoinParameters[T](self, items: Iterable[T], converter: Converter[T, str]) -> str:
        return ConditionalQueryBuilder.Join(Select(items, converter))
    @final
    def JoinParameters[T](self, items: Iterable[T]) -> str:
        return self._JoinParameters(items, self.GetParameter)
    @final
    def JoinOperands(self, items: Iterable[IOperandValue]) -> str:
        return ConditionalQueryBuilder.Join(Select(items, lambda operand: operand.Format(self)))
    
    @final
    def AddConditions(self, conditions: IParameterSetBase[IConditionalQueryWriter]|None) -> None:
        self._RenderConditions(" WHERE ", conditions, GetPrefixedConditionalQueryWriter)
    
    @final
    def ProcessCondition(self, condition: IKeyValuePair[IColumn, IArgument|None]) -> str:
        def process(column: str, parameter: IArgument|None) -> str:
            return column if parameter is None else parameter.Join(self, column)
        
        return process(condition.GetKey().ToString(self.FormatTableName), condition.GetValue())
    
    @final
    def ProcessConditions[T: IArgument](self, items: IDictionary[IColumn, T|None]) -> Generator[str]:            
        return Select(items.AsIterable(), self.ProcessCondition)
    
    @final
    def Build(self) -> DualResult[str, ICountableEnumerable[object]|None]:
        return DualResult[str, ICountableEnumerable[object]|None](self._GetStream().ToString(), CountableEnumerable[object].Create(self._GetArgs()))
    
    def Dispose(self):
        self._GetStream().Dispose()
class SelectionQueryBuilder(ConditionalQueryBuilder, ISelectionQueryBuilder):
    def __init__(self, query: IQueryBase[object]):
        super().__init__(query)
    
    @final
    def AddTable(self, name: str, parameter: ITableParameter[object]|None) -> str:
        def getAlias(parameter: ITableParameter[object]) -> str:
            alias: str|None = parameter.GetAlias()

            return '' if alias is None else f" AS {self.FormatTableName(alias)}"
        def getArguments(parameter: ITableParameter[object]) -> str:
            return f"{name}({self._JoinParameters(parameter.AsIterable(), lambda value: value.Render(self))})" # No name formating: routine.

        return self.FormatTableName(name) if parameter is None else f"{getArguments(parameter)}{getAlias(parameter)}"
    
    @final
    def AddJoins(self, joins: Iterable[IJoinBase[IParameterSetBase[ISelectionQueryWriter]]]|None) -> None:
        if joins is None:
            return
        
        for join in joins:
            self.Write(f" {join.GetType()} JOIN {self.AddTable(join.GetTableName(), join.GetTableParameter())}") # No name formating: can be routines.

            self._RenderConditions(" ON ", join.GetConditions(), GetPrefixedSelectionQueryWriter)