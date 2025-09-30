from __future__ import annotations

from abc import abstractmethod, ABC
from collections.abc import Iterable
from typing import final



from WinCopies import IInterface

from WinCopies.Collections import Enumeration, Generator, MakeSequence
from WinCopies.Collections.Abstraction.Collection import Dictionary
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, Enumerable
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Loop import DoForEachItem

from WinCopies.String import StringifyIfNone

from WinCopies.Typing import InvalidOperationError, IEquatableItem, IString
from WinCopies.Typing.Delegate import Selector
from WinCopies.Typing.Pairing import IKeyValuePair



from WinCopies.Data import IColumn, Column, TableColumn, IOperandValue
from WinCopies.Data.Misc import JoinType
from WinCopies.Data.Parameter import IParameter, ITableParameter
from WinCopies.Data.QueryBuilder import IJoinBase, IConditionalQueryWriter, ISelectionQueryWriter, IParameterSetBase
from WinCopies.Data.Set import IParameterSet, IColumnParameterSet, IFieldParameterSet, ITableParameterSet

class IConditionParameterSet(IParameterSetBase[IConditionalQueryWriter], IEnumerable[IFieldParameterSet[IParameter[IOperandValue]]]):
    def __init__(self):
        super().__init__()

class IBranchSet[T](IParameterSetBase[ISelectionQueryWriter]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetAlias(self) -> str:
        pass

    @abstractmethod
    def GetDefault(self) -> T:
        pass

class ICaseSet[TKey: IEquatableItem, TValue](IBranchSet[TKey]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumn(self) -> IColumn:
        pass
    
    @abstractmethod
    def GetConditions(self) -> IDictionary[TKey, TValue]:
        pass

class IExistenceQuery(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetTableName(self) -> str:
        pass
    
    @abstractmethod
    def GetTableParameter(self) -> ITableParameter[object]|None:
        pass

    @abstractmethod
    def GetJoins(self) -> Iterable[IJoin]|None:
        pass
    @abstractmethod
    def SetJoins(self, joins: Iterable[IJoin]|None) -> None:
        pass

    @abstractmethod
    def GetConditions(self) -> IConditionParameterSet|None:
        pass
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        pass
class ExistenceQuery(IExistenceQuery):
    def __init__(self, tableName: str, tableParameter: ITableParameter[object]|None, conditions: IConditionParameterSet|None = None):
        super().__init__()

        self.__tableName: str = tableName
        self.__tableParameter: ITableParameter[object]|None = tableParameter
        self.__conditions: IConditionParameterSet|None = conditions
        self.__joins: Iterable[IJoin]|None = None
    
    @final
    def GetTableName(self) -> str:
        return self.__tableName
    
    @final
    def GetTableParameter(self) -> ITableParameter[object]|None:
        return self.__tableParameter

    @abstractmethod
    def GetJoins(self) -> Iterable[IJoin]|None:
        return self.__joins
    @abstractmethod
    def SetJoins(self, joins: Iterable[IJoin]|None) -> None:
        self.__joins = joins
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None:
        return self.__conditions
    @final
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        self.__conditions = conditions

class IExistenceSet(IBranchSet[bool]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetQuery(self) -> IExistenceQuery:
        pass

class IMatchSet[T: IEquatableItem](ICaseSet[T, T]):
    def __init__(self):
        super().__init__()
class IConditionSet[T: IEquatableItem](ICaseSet[T, IParameter[object]]):
    def __init__(self):
        super().__init__()
class IIfSet[T: IEquatableItem](ICaseSet[T, IConditionParameterSet]):
    def __init__(self):
        super().__init__()

class ParameterSet[T](Dictionary[IColumn, T], IParameterSet[T]):
    def __init__(self, dictionary: dict[IColumn, T]|None = None):
        super().__init__(dictionary)

class ColumnParameterSet[T: IParameter[object]](ParameterSet[T|None], IColumnParameterSet[T]):
    def __init__(self, dictionary: dict[IColumn, T|None]|None = None):
        super().__init__(dictionary)
    
    @staticmethod
    def Create(columns: Iterable[IColumn]) -> IColumnParameterSet[T]:
        return ColumnParameterSet(dict.fromkeys(columns))
    
    @staticmethod
    def CreateFromNames(columnNames: Iterable[str], tableName: str|None = None) -> IColumnParameterSet[T]:
        return ColumnParameterSet[T].Create(Select(columnNames, (lambda columnName: Column(columnName)) if tableName is None else (lambda columnName: TableColumn(tableName, columnName))))
class FieldParameterSet[T: IParameter[IOperandValue]](ParameterSet[T], IFieldParameterSet[T]):
    def __init__(self, dictionary: dict[IColumn, T]|None = None):
        super().__init__(dictionary)

def MakeFieldParameterSetIterable[T: IParameter[IOperandValue]](*dictionaries: dict[IColumn, T]|None) -> Generator[IFieldParameterSet[T]]:
    return (FieldParameterSet[T](dictionary) for dictionary in dictionaries)

class TableParameterSet(Dictionary[IString, ITableParameter[object]|None], ITableParameterSet):
    def __init__(self, dictionary: dict[IString, ITableParameter[object]|None]|None = None):
        super().__init__(dictionary)
    
    @staticmethod
    def Create(tableNames: Iterable[IString]) -> ITableParameterSet:
        return TableParameterSet(dict.fromkeys(tableNames))

class ConditionParameterSetBase(Enumerable[IFieldParameterSet[IParameter[IOperandValue]]], IConditionParameterSet):
    def __init__(self):
        super().__init__()
    
    @final
    def Render(self, writer: IConditionalQueryWriter) -> None:
        def joinConditions(operator: str, values: Iterable[str]) -> str:
            return f" {operator} ".join(values)
        
        writer.Write(joinConditions("OR", (f"({joinConditions("AND", writer.ProcessConditions(dic))})" for dic in self.AsIterable())))
class ConditionParameterSet(ConditionParameterSetBase):
    def __init__(self, conditions: Iterable[IFieldParameterSet[IParameter[IOperandValue]]]):
        super().__init__()

        self.__conditions: IEnumerable[IFieldParameterSet[IParameter[IOperandValue]]] = Enumeration.Iterable[IFieldParameterSet[IParameter[IOperandValue]]].Create(conditions)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IFieldParameterSet[IParameter[IOperandValue]]]|None:
        return self.__conditions.TryGetEnumerator()

class BranchSetBase[T](ABC, IBranchSet[T]):
    def __init__(self, alias: str):
        super().__init__()

        self.__alias: str = alias
    
    @final
    def GetAlias(self) -> str:
        return self.__alias
    
    @abstractmethod
    def _GetColumn(self) -> str|None:
        pass

    @abstractmethod
    def _WriteConditions(self, writer: ISelectionQueryWriter) -> None:
        pass
    
    @final
    def Render(self, writer: ISelectionQueryWriter) -> None:
        def getColumnName() -> str:
            columnName: str = StringifyIfNone(self._GetColumn())

            return '' if columnName == '' else ' ' + columnName
        
        writer.Write(f"CASE{getColumnName()} WHEN ")
        
        self._WriteConditions(writer)
        
        writer.Write(f" ELSE {writer.JoinParameters(MakeSequence(self.GetDefault()))} END AS {writer.FormatTableName(self.GetAlias())}")
class BranchSet[T](BranchSetBase[T]):
    def __init__(self, alias: str, defaultValue: T):
        super().__init__(alias)

        self.__defaultValue: T = defaultValue
    
    @final
    def GetDefault(self) -> T:
        return self.__defaultValue

class ExistenceSet(BranchSetBase[bool], IExistenceSet):
    def __init__(self, alias: str, query: IExistenceQuery):
        super().__init__(alias)

        self.__query: IExistenceQuery = query
    
    @final
    def _GetColumn(self) -> None:
        return None
    
    @final
    def _WriteConditions(self, writer: ISelectionQueryWriter) -> None:
        query: IExistenceQuery = self.GetQuery()

        writer.Write(f"(SELECT 1 FROM {writer.AddTable(query.GetTableName(), query.GetTableParameter())}")

        writer.AddJoins(query.GetJoins())
        writer.AddConditions(query.GetConditions())

        writer.Write(") THEN 1")
    
    @final
    def GetDefault(self) -> bool:
        return False
    
    @final
    def GetQuery(self) -> IExistenceQuery:
        return self.__query

class CaseSet[TKey: IEquatableItem, TValue](BranchSet[TKey], ICaseSet[TKey, TValue]):
    def __init__(self, alias: str, defaultValue: TKey, column: IColumn, conditions: IDictionary[TKey, TValue]|None = None):
        super().__init__(alias, defaultValue)

        self.__column: IColumn = column
        self.__conditions: IDictionary[TKey, TValue] = Dictionary[TKey, TValue]() if conditions is None else conditions
    
    @abstractmethod
    def _RenderValue(self, value: TValue, writer: ISelectionQueryWriter) -> None:
        pass

    @final
    def _WriteConditions(self, writer: ISelectionQueryWriter) -> None:
        def render(item: IKeyValuePair[TKey, TValue]) -> None:
            self._RenderValue(item.GetValue(), writer)

            writer.Write(f" THEN {writer.JoinParameters(MakeSequence(item.GetKey()))}")

        if not DoForEachItem(self.GetConditions().AsIterable(), render):
            raise ValueError("No condition given.")
    
    @final
    def GetColumn(self) -> IColumn:
        return self.__column
    
    @final
    def GetConditions(self) -> IDictionary[TKey, TValue]:
        return self.__conditions

class MatchSet[T: IEquatableItem](CaseSet[T, T], IMatchSet[T]):
    def __init__(self, alias: str, defaultValue: T, column: IColumn, dictionary: IDictionary[T, T]|None = None):
        super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _GetColumn(self) -> str:
        return f"{self.GetColumn()}"
    
    @final
    def _RenderValue(self, value: T, writer: ISelectionQueryWriter) -> None:
        writer.Write(writer.JoinParameters(MakeSequence(value)))

class ConditionalSet[TKey: IEquatableItem, TValue](CaseSet[TKey, TValue]):
    def __init__(self, alias: str, defaultValue: TKey, column: IColumn, dictionary: IDictionary[TKey, TValue]|None = None):
        super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _GetColumn(self) -> None:
        return None

class ConditionSet[T: IEquatableItem](ConditionalSet[T, IParameter[object]], IConditionSet[T]):
    def __init__(self, alias: str, defaultValue: T, column: IColumn, dictionary: IDictionary[T, IParameter[object]]|None = None):
        super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _RenderValue(self, value: IParameter[object], writer: ISelectionQueryWriter) -> None:
        def getArgument(arguments: Iterable[object]) -> Generator[object]:
            func: Selector[object]|None = None

            def getArgument(argument: object) -> object:
                nonlocal func

                def throw(_: object) -> None:
                    raise InvalidOperationError("Only one argument must be given in Case statements.")

                func = throw

                return argument
            
            func = getArgument

            for argument in arguments:
                yield func(argument)
        
        writer.Write(value.Format(self.GetColumn().ToString(writer.FormatTableName), writer.JoinParameters(getArgument(value.AsIterable()))))
class IfSet[T: IEquatableItem](ConditionalSet[T, IConditionParameterSet], IIfSet[T]):
    def __init__(self, alias: str, defaultValue: T, column: IColumn, dictionary: IDictionary[T, IConditionParameterSet]|None = None):
        super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _RenderValue(self, value: IConditionParameterSet, writer: ISelectionQueryWriter) -> None:
        value.Render(writer)

class IJoin(IJoinBase[IConditionParameterSet]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        pass
class Join(IJoin):
    def __init__(self, type: JoinType, tableName: str, tableParameter: ITableParameter[object], conditions: IConditionParameterSet|None = None):
        super().__init__()

        self.__type: JoinType = type
        self.__tableName: str = tableName
        self.__tableParameter: ITableParameter[object] = tableParameter
        self.__conditions: IConditionParameterSet|None = conditions
    
    @final
    def GetType(self) -> JoinType:
        return self.__type
    
    @final
    def GetTableName(self) -> str:
        return self.__tableName
    
    @final
    def GetTableParameter(self) -> ITableParameter[object]:
        return self.__tableParameter
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None:
        return self.__conditions
    @final
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        self.__conditions = conditions