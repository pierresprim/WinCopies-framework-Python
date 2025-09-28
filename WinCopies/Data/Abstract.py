from __future__ import annotations

from abc import abstractmethod, ABC
from collections.abc import Iterable
from typing import final, Self

from WinCopies import IDisposable

from WinCopies.Collections import Generator, MakeSequence
from WinCopies.Collections.Abstraction.Collection import List, Dictionary
from WinCopies.Collections.Enumeration import ICountableEnumerable
from WinCopies.Collections.Extensions import IArray, IList, IDictionary

from WinCopies.Typing import IEquatable, IString, String, IType, Type, GetDisposedError
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Pairing import DualValueNullableInfo
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

from WinCopies.Data.Factory import IFieldFactory, IQueryFactory
from WinCopies.Data.Field import IField
from WinCopies.Data.Index import IIndex
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.Query import ISelectionQuery, IInsertionQuery, IMultiInsertionQuery, IUpdateQuery, ISelectionQueryExecutionResult, IInsertionQueryExecutionResult
from WinCopies.Data.Set import IColumnParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet, TableParameterSet

class ITable(IEquatable['ITable'], IDisposable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetName(self) -> str:
        pass
    @abstractmethod
    def SetName(self, name: str) -> None:
        pass

    @abstractmethod
    def GetFields(self) -> IArray[IField]:
        pass

    @abstractmethod
    def GetSelectionQuery(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQuery:
        pass
    
    @abstractmethod
    def GetInsertionQuery(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
        pass
    @abstractmethod
    def GetMultipleInsertionQuery(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
        pass

    @abstractmethod
    def GetUpdateQuery(self, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> IUpdateQuery:
        pass

    @final
    def Select(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQueryExecutionResult|None:
        return self.GetSelectionQuery(columns).Execute()
    
    @final
    def Insert(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult:
        return self.GetInsertionQuery(items, ignoreExisting).Execute()
    @final
    def InsertMultiple(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult:
        return self.GetMultipleInsertionQuery(columns, items, ignoreExisting).Execute()
    
    @final
    def Update(self, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> IInsertionQueryExecutionResult:
        return self.GetUpdateQuery(values, conditions).Execute()
    
    @abstractmethod
    def Remove(self) -> None:
        pass

class Table(ABC, ITable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetConnection(self) -> IConnection:
        pass
    
    def Equals(self, item: ITable|object) -> bool:
        return item is self
    
    @final
    def GetSelectionQuery(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQuery:
        return self._GetConnection().GetQueryFactory().GetSelectionQuery(TableParameterSet.Create(MakeSequence(String(self.GetName()))), columns)
    
    @final
    def GetInsertionQuery(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
        return self._GetConnection().GetQueryFactory().GetInsertionQuery(self.GetName(), items, ignoreExisting)
    @final
    def GetMultipleInsertionQuery(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
        return self._GetConnection().GetQueryFactory().GetMultiInsertionQuery(self.GetName(), columns, items, ignoreExisting)

    @final
    def GetUpdateQuery(self, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> IUpdateQuery:
        return self._GetConnection().GetQueryFactory().GetUpdateQuery(self.GetName(), values, conditions)

class IConnection(IDisposable):
    def __init__(self):
        pass

    def Initialize(self) -> None:
        self.Open()
    
    @abstractmethod
    def Open(self) -> bool:
        pass

    @abstractmethod
    def FormatTableName(self, name: str) -> str:
        pass

    @abstractmethod
    def GetQueryFactory(self) -> IQueryFactory:
        pass
    @abstractmethod
    def GetFieldFactory(self) -> IFieldFactory:
        pass
    
    @abstractmethod
    def GetTableNames(self) -> Iterable[str]:
        pass

    @abstractmethod
    def TryCreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable:
        pass
    @abstractmethod
    def CreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable:
        pass

    @abstractmethod
    def TryGetTable(self, name: str) -> ITable|None:
        pass
    
    @abstractmethod
    def GetTables(self) -> Generator[ITable]:
        pass
    
    @abstractmethod
    def Commit(self) -> bool:
        pass

    @abstractmethod
    def Close(self) -> None:
        pass

    def Dispose(self) -> None:
        self.Close()

class Connection(IConnection):
    @final
    class NullTable(ITable):
        def __init__(self):
            super().__init__()
        
        def Equals(self, item: ITable|object) -> bool:
            return item is self or isinstance(item, ITable)
        
        def GetName(self) -> str:
            raise GetDisposedError()
        def SetName(self, name: str) -> None:
            raise GetDisposedError()
        
        def GetFields(self) -> IArray[IField]:
            raise GetDisposedError()
        
        def GetSelectionQuery(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQuery:
            raise GetDisposedError()
        
        def GetInsertionQuery(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
            raise GetDisposedError()
        def GetMultipleInsertionQuery(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
            raise GetDisposedError()
        
        def GetUpdateQuery(self, values: IDictionary[IString, object], conditions: IConditionParameterSet | None) -> IUpdateQuery:
            raise GetDisposedError()
        
        def Remove(self) -> None:
            raise GetDisposedError()
        
        def Dispose(self) -> None:
            pass
    @final
    class Table(ITable):
        def __init__(self, tableList: IList[Connection.Table], table: ITable):
            EnsureDirectModuleCall()

            super().__init__()
            
            self.__tableList: IList[Connection.Table]|None = tableList
            self.__table: ITable = table
        
        def Equals(self, item: ITable|object) -> bool:
            return isinstance(item, Connection.Table) and self.__tableList == item.__tableList and self.GetName() == item.GetName()
        
        def GetName(self) -> str:
            return self.__table.GetName()
        def SetName(self, name: str) -> None:
            self.__table.SetName(name)
        
        def GetFields(self) -> IArray[IField]:
            return self.__table.GetFields()
        
        def GetSelectionQuery(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQuery:
            return self.__table.GetSelectionQuery(columns)
        
        def GetInsertionQuery(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
            return self.__table.GetInsertionQuery(items, ignoreExisting)
        def GetMultipleInsertionQuery(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
            return self.__table.GetMultipleInsertionQuery(columns, items, ignoreExisting)
        
        def GetUpdateQuery(self, values: IDictionary[IString, object], conditions: IConditionParameterSet | None) -> IUpdateQuery:
            return self.__table.GetUpdateQuery(values, conditions)
        
        def Remove(self) -> None:
            self.__table.Remove()
        
        def Dispose(self) -> None:
            if self.__tableList is None:
                return
            
            self.__table.Dispose()

            self.__tableList.Remove(self)
            self.__tableList = None
            
            self.__table = Connection._GetNullTable()
    
    __table: ITable = NullTable()

    __fieldFactories: IDictionary[IType[Connection], IFieldFactory] = Dictionary[IType[Self], IFieldFactory]()
    __queryFactories: IDictionary[IType[Connection], IQueryFactory] = Dictionary[IType[Self], IQueryFactory]()

    @staticmethod
    def _GetNullTable() -> ITable:
        return Connection.__table
    
    def __init__(self):
        super().__init__()

        self.__tables: List[Connection.Table] = List[Connection.Table]()
    
    @final
    def __TryGetFactory[T](self, dictionary: IDictionary[IType[Connection], T]) -> DualValueNullableInfo[IType[Connection], T]:
        t: IType[Connection] = Type[Connection].Create(self)

        return DualValueNullableInfo[IType[Connection], T](t, dictionary.TryGetAt(t, None))
    @final
    def __GetFactory[T](self, factories: IDictionary[IType[Connection], T], func: Function[T]) -> T:
        result: DualValueNullableInfo[IType[Connection], T|None] = self.__TryGetFactory(factories)

        factory: T|None = result.GetValue()

        if factory is None:
            factories.Add(result.GetKey(), factory := func())
        
        return factory
    
    @abstractmethod
    def _GetFieldFactory(self) -> IFieldFactory:
        pass
    @abstractmethod
    def _GetQueryFactory(self) -> IQueryFactory:
        pass

    @final
    def GetFieldFactory(self) -> IFieldFactory:
        return self.__GetFactory(Connection.__fieldFactories, self._GetFieldFactory)
    @final
    def GetQueryFactory(self) -> IQueryFactory:
        return self.__GetFactory(Connection.__queryFactories, self._GetQueryFactory)
    
    @abstractmethod
    def _GetTable(self, name: str) -> ITable:
        pass

    @final
    def __TryGetTable(self, tableName: str) -> ITable|None:
        for table in self.__tables:
            if table.GetName() == tableName:
                return table
        
        return None
    
    @final
    def __AddNewTable(self, table: ITable) -> ITable:
        _table: Connection.Table = Connection.Table(self.__tables, table)
        
        self.__tables.Add(_table)

        return _table
    @final
    def __AddTable(self, name: str) -> ITable:
        return self.__AddNewTable(self._GetTable(name))
    
    @abstractmethod
    def _TryCreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable|None:
        pass
    @abstractmethod
    def _CreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable:
        pass

    @final
    def TryCreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable:
        table: ITable|None = self._TryCreateTableOverride(name, fields, indices)
        
        return self.__AddTable(name) if table is None else self.__AddNewTable(table)
    @final
    def CreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable:
        return self.__AddNewTable(self._CreateTableOverride(name, fields, indices))
    
    @final
    def TryGetTable(self, name: str) -> ITable|None:
        table: ITable|None = self.__TryGetTable(name)

        return self.__AddTable(name) if table is None and name in self.GetTableNames() else table
    
    @final
    def GetTables(self) -> Generator[ITable]:
        table: ITable|None = None
        
        for name in self.GetTableNames():
            if (table := self.__TryGetTable(name)) is None:
                table = self.__AddTable(name)
            
            yield table
    
    @abstractmethod
    def _CloseOverride(self) -> None:
        pass
    
    @final
    def Close(self) -> None:
        for table in self.__tables:
            table.Dispose()
        
        self._CloseOverride()