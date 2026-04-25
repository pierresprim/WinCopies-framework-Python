from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final



from WinCopies import IDisposable, Abstract

from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction.Collection import List
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IteratorProvider
from WinCopies.Collections.Extensions import IArray, IList, IDictionary, IReadOnlyKeyedSet
from WinCopies.Collections.Iteration import GetFirstItem, SelectWhereNotNone

from WinCopies.Typing import IEquatable, INullable, GetDisposedError
from WinCopies.Typing.Object import IString
from WinCopies.Typing.Reflection import EnsureDirectModuleCall



from WinCopies.Data.Factory import IFieldFactory, IQueryFactory, ITableQueryFactory, IIndexFactory
from WinCopies.Data.Field import IField
from WinCopies.Data.Index import IIndex
from WinCopies.Data.Parameter import IFormattable
from WinCopies.Data.Query import IQueryLimits, ISelectionQuery, IInsertionQuery, IMultiInsertionQuery, IUpdateQuery, ISelectionQueryExecutionResult, IInsertionQueryExecutionResult
from WinCopies.Data.Set import IColumnParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet

class ITable(IEquatable['ITable'], IDisposable):
    def __init__(self) -> None:
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
    def GetIndices(self) -> IArray[IIndex]:
        pass

    @abstractmethod
    def GetQueryFactory(self) -> ITableQueryFactory:
        pass

    @final
    def Select(self, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None = None) -> ISelectionQueryExecutionResult|None:
        return self.GetQueryFactory().GetSelectionQuery(columns, conditions).Execute()
    @abstractmethod
    def SelectByKeys(self, columns: IColumnParameterSet[IFormattable], keys: IReadOnlyKeyedSet[IString, object]) -> Generator[ISelectionQueryExecutionResult]|None:
        pass
    
    @final
    def Insert(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult:
        return self.GetQueryFactory().GetInsertionQuery(items, ignoreExisting).Execute()
    @final
    def InsertMultiple(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult:
        return self.GetQueryFactory().GetMultiInsertionQuery(columns, items, ignoreExisting).Execute()
    
    @final
    def Update(self, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> IInsertionQueryExecutionResult:
        return self.GetQueryFactory().GetUpdateQuery(values, conditions).Execute()
    
    @abstractmethod
    def Remove(self) -> None:
        pass

class Table(Abstract, ITable):
    class _QueryFactory(Abstract, ITableQueryFactory):
        def __init__(self, table: Table) -> None:
            super().__init__()

            self.__table: Table = table
            self.__factory: IQueryFactory = table._GetConnection().GetQueryFactory()
        
        @final
        def _GetTable(self) -> Table:
            return self.__table
        @final
        def _GetFactory(self) -> IQueryFactory:
            return self.__factory
        
        @final
        def TryBuildConditionsByKeys(self, keys: IReadOnlyKeyedSet[IString, object], maxParameterCount: int|None = None) -> Generator[IConditionParameterSet]|None:
            return self._GetFactory().TryBuildConditionsByKeys(keys, maxParameterCount)

        @final
        def GetSelectionQuery(self, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None = None) -> ISelectionQuery:
            return self._GetFactory().GetSelectionQuery(self._GetTable().GetName(), columns, conditions)

        @final
        def GetInsertionQuery(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
            return self._GetFactory().GetInsertionQuery(self._GetTable().GetName(), items, ignoreExisting)
        @final
        def GetMultiInsertionQuery(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
            return self._GetFactory().GetMultiInsertionQuery(self._GetTable().GetName(), columns, items, ignoreExisting)
        
        @final
        def GetUpdateQuery(self, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> IUpdateQuery:
            return self._GetFactory().GetUpdateQuery(self._GetTable().GetName(), values, conditions)
    
    def __init__(self) -> None:
        super().__init__()

        self.__queryFactory: ITableQueryFactory|None = None
    
    @abstractmethod
    def _GetConnection(self) -> IConnection:
        pass
    
    @final
    def GetQueryFactory(self) -> ITableQueryFactory:
        if self.__queryFactory is None:
            self.__queryFactory = Table._QueryFactory(self)
        
        return self.__queryFactory
    
    @final
    def SelectByKeys(self, columns: IColumnParameterSet[IFormattable], keys: IReadOnlyKeyedSet[IString, object]) -> Generator[ISelectionQueryExecutionResult]|None:
        def select(conditionSet: IConditionParameterSet) -> ISelectionQueryExecutionResult|None:
            query.SetConditions(conditionSet)

            return query.Execute()

        factory: ITableQueryFactory = self.GetQueryFactory()
        conditions: Generator[IConditionParameterSet]|None = factory.TryBuildConditionsByKeys(keys, self._GetConnection().GetQueryLimits().GetMaxParameterCount())

        if conditions is None:
            return None
        
        query: ISelectionQuery = factory.GetSelectionQuery(columns)
        
        return SelectWhereNotNone(conditions, select)
    
    def Equals(self, item: ITable|object) -> bool:
        return item is self

class IConnection(IDisposable):
    def __init__(self) -> None:
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
    def GetQueryLimits(self) -> IQueryLimits:
        pass

    @abstractmethod
    def GetQueryFactory(self) -> IQueryFactory:
        pass
    @abstractmethod
    def GetFieldFactory(self) -> IFieldFactory:
        pass
    @abstractmethod
    def GetIndexFactory(self) -> IIndexFactory:
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
    def EnumerateTables(self) -> Generator[ITable]:
        pass
    @abstractmethod
    def GetTables(self) -> IEnumerable[ITable]:
        pass
    
    @abstractmethod
    def Commit(self) -> bool:
        pass

    @abstractmethod
    def Close(self) -> None:
        pass

    def Dispose(self) -> None:
        self.Close()

class Connection(Abstract, IConnection):
    @final
    class __Factories(Abstract):
        def __init__(self) -> None:
            super().__init__()

            self.Field: IFieldFactory|None = None
            self.Query: IQueryFactory|None = None
            self.Index: IIndexFactory|None = None
    @final
    class __NullTable(Abstract, ITable):
        def __init__(self) -> None:
            super().__init__()
        
        def Equals(self, item: ITable|object) -> bool:
            return item is self or isinstance(item, ITable)
        
        def GetName(self) -> str:
            raise GetDisposedError()
        def SetName(self, name: str) -> None:
            raise GetDisposedError()

        def GetQueryFactory(self) -> ITableQueryFactory:
            raise GetDisposedError()
        
        def GetFields(self) -> IArray[IField]:
            raise GetDisposedError()

        def GetIndices(self) -> IArray[IIndex]:
            raise GetDisposedError()
        
        def SelectByKeys(self, columns: IColumnParameterSet[IFormattable], keys: IReadOnlyKeyedSet[IString, object]) -> Generator[ISelectionQueryExecutionResult]|None:
            raise GetDisposedError()
        
        def Remove(self) -> None:
            raise GetDisposedError()
        
        def Dispose(self) -> None:
            pass
    @final
    class _Table(Abstract, ITable):
        def __init__(self, tableList: IList[Connection._Table], table: ITable) -> None:
            EnsureDirectModuleCall()

            super().__init__()
            
            self.__tableList: IList[Connection._Table]|None = tableList
            self.__table: ITable = table
        
        def Equals(self, item: ITable|object) -> bool:
            return isinstance(item, Connection._Table) and self.__tableList == item.__tableList and self.GetName() == item.GetName()
        
        def GetName(self) -> str:
            return self.__table.GetName()
        def SetName(self, name: str) -> None:
            self.__table.SetName(name)

        def GetQueryFactory(self) -> ITableQueryFactory:
            return self.__table.GetQueryFactory()

        def GetIndices(self) -> IArray[IIndex]:
            return self.__table.GetIndices()
        
        def GetFields(self) -> IArray[IField]:
            return self.__table.GetFields()
        
        def SelectByKeys(self, columns: IColumnParameterSet[IFormattable], keys: IReadOnlyKeyedSet[IString, object]) -> Generator[ISelectionQueryExecutionResult]|None:
            return self.__table.SelectByKeys(columns, keys)
        
        def Remove(self) -> None:
            self.__table.Remove()
        
        def Dispose(self) -> None:
            if self.__tableList is None:
                return
            
            self.__table.Dispose()

            self.__tableList.Remove(self)
            self.__tableList = None
            
            self.__table = Connection._GetNullTable()
    
    __table: ITable = __NullTable()

    @staticmethod
    def _GetNullTable() -> ITable:
        return Connection.__table
    
    def __init__(self) -> None:
        super().__init__()

        self.__tables: List[Connection._Table] = List[Connection._Table]()

        self.__factories: Connection.__Factories = Connection.__Factories()
    
    @abstractmethod
    def _GetFieldFactory(self) -> IFieldFactory:
        pass
    @abstractmethod
    def _GetQueryFactory(self) -> IQueryFactory:
        pass
    @abstractmethod
    def _GetIndexFactory(self) -> IIndexFactory:
        pass

    @final
    def GetFieldFactory(self) -> IFieldFactory:
        if self.__factories.Field is None:
            self.__factories.Field = self._GetFieldFactory()
        
        return self.__factories.Field
    @final
    def GetQueryFactory(self) -> IQueryFactory:
        if self.__factories.Query is None:
            self.__factories.Query = self._GetQueryFactory()
        
        return self.__factories.Query
    @final
    def GetIndexFactory(self) -> IIndexFactory:
        if self.__factories.Index is None:
            self.__factories.Index = self._GetIndexFactory()
        
        return self.__factories.Index
    
    @abstractmethod
    def _GetTable(self, name: str) -> ITable:
        pass

    @final
    def __TryGetTable(self, tableName: str) -> ITable|None:
        return GetFirstItem(self.__tables, lambda table: table.GetName() == tableName).TryGetValue()
    
    @final
    def __AddNewTable(self, table: ITable) -> ITable:
        _table: Connection._Table = Connection._Table(self.__tables, table)
        
        self.__tables.Add(_table)

        return _table
    @final
    def __AddTable(self, name: str) -> ITable:
        return self.__AddNewTable(self._GetTable(name))
    
    @abstractmethod
    def _TryCreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> INullable[ITable]|None:
        pass
    @abstractmethod
    def _CreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable:
        pass

    @final
    def TryCreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable:
        def addTable() -> ITable:
            return self.__AddTable(name)
        
        def getTable(table: ITable|None) -> ITable:
            return addTable() if table is None else self.__AddNewTable(table)
        def tryGetTable() -> ITable:
            table: ITable|None = self.__TryGetTable(name)

            return addTable() if table is None else table
        
        table: INullable[ITable]|None = self._TryCreateTableOverride(name, fields, indices)
        
        return tryGetTable() if table is None else getTable(table.TryGetValue())
    @final
    def CreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable:
        return self.__AddNewTable(self._CreateTableOverride(name, fields, indices))
    
    @final
    def TryGetTable(self, name: str) -> ITable|None:
        table: ITable|None = self.__TryGetTable(name)

        return self.__AddTable(name) if table is None and name in self.GetTableNames() else table
    
    @final
    def EnumerateTables(self) -> Generator[ITable]:
        table: ITable|None = None
        
        for name in self.GetTableNames():
            if (table := self.__TryGetTable(name)) is None:
                table = self.__AddTable(name)
            
            yield table
    @final
    def GetTables(self) -> IEnumerable[ITable]:
        return IteratorProvider[ITable](self.EnumerateTables)
    
    @abstractmethod
    def _CloseOverride(self) -> None:
        pass
    
    @final
    def Close(self) -> None:
        for table in self.__tables:
            table.Dispose()
        
        self._CloseOverride()