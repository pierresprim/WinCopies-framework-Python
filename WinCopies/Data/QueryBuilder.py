from __future__ import annotations


from abc import abstractmethod
from collections.abc import Iterable
from typing import final



from WinCopies import IInterface

from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction import CountableIterable
from WinCopies.Collections.Enumeration import ICountableIterable
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Singly import CountableIterableQueue

from WinCopies.IO.Stream import MemoryTextStream

from WinCopies.Typing.Delegate import Converter, Method
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult



from WinCopies.Data import IOperandValue, IColumn, IQueryBuilder
from WinCopies.Data.Misc import JoinType, IQueryBase
from WinCopies.Data.Parameter import IArgument
from WinCopies.Data.Set import ITableParameter

class IParameterSetBase(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Render(self, writer: ISelectionQueryWriter) -> None:
        pass

class IJoinBase[T: IParameterSetBase](IInterface):
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

class ISelectionQueryWriter(IQueryBuilder):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def OpenStream(self) -> None:
        pass

    @abstractmethod
    def Write(self, value: str) -> None:
        pass

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
    def AddJoins(self, joins: Iterable[IJoinBase[IParameterSetBase]]|None) -> None:
        pass
    
    @abstractmethod
    def AddConditions(self, conditions: IParameterSetBase|None) -> None:
        pass
    
    @abstractmethod
    def ProcessCondition(self, condition: IKeyValuePair[IColumn, IArgument|None]) -> str:
        pass
    
    @abstractmethod
    def ProcessConditions[T: IArgument|None](self, items: IDictionary[IColumn, T]) -> Generator[str]:
        pass

class ISelectionQueryBuilder(ISelectionQueryWriter):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def Build(self) -> DualResult[str, ICountableIterable[object]|None]:
        pass

@final
class __SelectionQueryWriter(ISelectionQueryWriter):
    def __init__(self, prefix: str, writer: ISelectionQueryWriter):
        def write(value: str) -> None:
            def write(value: str) -> None:
                self.__builder.Write(value)
            
            write(prefix + value)
            
            self.__write = write
        
        super().__init__()

        self.__builder: ISelectionQueryWriter = writer
        self.__write: Method[str] = write
    
    def FormatTableName(self, name: str) -> str:
        return self.__builder.FormatTableName(name)
    
    def OpenStream(self) -> None:
        self.__builder.OpenStream()

    def Write(self, value: str) -> None:
        return self.__write(value)

    def JoinParameters[T](self, items: Iterable[T]) -> str:
        return self.__builder.JoinParameters(items)
    def JoinOperands(self, items: Iterable[IOperandValue]) -> str:
        return self.__builder.JoinOperands(items)

    def AddTable(self, name: str, parameter: ITableParameter[object]|None) -> str:
        return self.__builder.AddTable(name, parameter)

    def AddJoins(self, joins: Iterable[IJoinBase[IParameterSetBase]]|None) -> None:
        return self.__builder.AddJoins(joins)
    
    def AddConditions(self, conditions: IParameterSetBase|None) -> None:
        return self.__builder.AddConditions(conditions)
    
    def ProcessCondition(self, condition: IKeyValuePair[IColumn, IArgument|None]) -> str:
        return self.__builder.ProcessCondition(condition)
    
    def ProcessConditions(self, items: IDictionary[IColumn, IArgument|None]) -> Generator[str]:
        return self.__builder.ProcessConditions(items)

def GetPrefixedSelectionQueryWriter(prefix: str, writer: ISelectionQueryWriter) -> ISelectionQueryWriter:
    return __SelectionQueryWriter(prefix, writer)

class SelectionQueryBuilderBase[T: IQueryBase[object]](ISelectionQueryBuilder):
    def __init__(self, query: T):
        super().__init__()

        self.__query: T = query
    
    @final
    def _GetQuery(self) -> T:
        return self.__query
class SelectionQueryBuilder(SelectionQueryBuilderBase[IQueryBase[object]]):
    def __init__(self, query: IQueryBase[object]):
        super().__init__(query)

        self.__stream: MemoryTextStream = MemoryTextStream()
        self.__args: CountableIterableQueue[object] = CountableIterableQueue[object]()
    
    @final
    def OpenStream(self) -> None:
        self.__stream.Open()
    
    @final
    def Write(self, value: str) -> None:
        self.__stream.Write(value)
    
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
    def __Push(self, arg: object) -> None:
        """
        Add a given value to the list of query arguments.

        Parameters:
        - arg: The argument to add.
        """
        self.__args.Push(arg)
    
    @final
    def GetParameter(self, arg: object|None) -> str:
        if arg is None:
            return "NULL"
        
        self.__Push(arg)
        
        return '?'
    
    @final
    def __JoinParameters[T](self, items: Iterable[T], converter: Converter[T, str]) -> str:
        return SelectionQueryBuilder.Join(Select(items, converter))
    @final
    def JoinParameters[T](self, items: Iterable[T]) -> str:
        return self.__JoinParameters(items, self.GetParameter)
    @final
    def JoinOperands(self, items: Iterable[IOperandValue]) -> str:
        return SelectionQueryBuilder.Join(Select(items, lambda operand: operand.Format(self)))
    
    @final
    def FormatTableName(self, name: str) -> str:
        return self._GetQuery().FormatTableName(name)
    
    @final
    def AddTable(self, name: str, parameter: ITableParameter[object]|None) -> str:
        def getAlias(parameter: ITableParameter[object]) -> str:
            alias: str|None = parameter.GetAlias()

            return '' if alias is None else f" AS {self.FormatTableName(alias)}"
        def getArguments(parameter: ITableParameter[object]) -> str:
            return f"{name}({self.__JoinParameters(parameter, lambda value: value.Render(self))})" # No name formatting: routine.

        return self.FormatTableName(name) if parameter is None else f"{getArguments(parameter)}{getAlias(parameter)}"
    
    @final
    def __RenderConditions(self, prefix: str, conditions: IParameterSetBase|None) -> None:
        if conditions is None:
            return
        
        conditions.Render(GetPrefixedSelectionQueryWriter(prefix, self))
    
    @final
    def AddJoins(self, joins: Iterable[IJoinBase[IParameterSetBase]]|None) -> None:
        if joins is None:
            return
        
        for join in joins:
            self.Write(f" {join.GetType()} JOIN {self.AddTable(join.GetTableName(), join.GetTableParameter())}") # No name formatting: can be routines.

            self.__RenderConditions(" ON ", join.GetConditions())
    
    @final
    def AddConditions(self, conditions: IParameterSetBase|None) -> None:
        self.__RenderConditions(" WHERE ", conditions)
    
    @final
    def ProcessCondition(self, condition: IKeyValuePair[IColumn, IArgument|None]) -> str:
        def process(column: str, parameter: IArgument|None) -> str:
            return column if parameter is None else parameter.Join(self, column)
        
        return process(condition.GetKey().ToString(self.FormatTableName), condition.GetValue())
    
    @final
    def ProcessConditions[T: IArgument](self, items: IDictionary[IColumn, T|None]) -> Generator[str]:            
        return (self.ProcessCondition(item) for item in items)
    
    @final
    def Build(self) -> DualResult[str, ICountableIterable[object]|None]:
        r=self.__stream.ToString()
        print(r)
        return DualResult[str, ICountableIterable[object]|None](r, CountableIterable[object].Create(self.__args))
    
    def Dispose(self):
        self.__stream.Dispose()