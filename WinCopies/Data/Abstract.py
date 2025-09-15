from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final, Self

from WinCopies import IDisposable

from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction import List, Dictionary
from WinCopies.Collections.Extensions import IArray, IList, IDictionary

from WinCopies.Data.Factory import IFieldFactory, IQueryFactory
from WinCopies.Data.Field import IField
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.Query import ISelectionQueryExecutionResult, IInsertionQueryExecutionResult
from WinCopies.Data.Set import IColumnParameterSet

from WinCopies.Typing import IEquatable, GetDisposedError
from WinCopies.Typing.Pairing import DualValueNullableInfo
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class ITable(IDisposable, IEquatable['ITable']):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetName(self) -> str:
        pass

    @abstractmethod
    def GetFields(self) -> IArray[IField]:
        pass

    @abstractmethod
    def Select(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQueryExecutionResult|None:
        pass
    
    @abstractmethod
    def Insert(self, items: IDictionary[str, object]) -> IInsertionQueryExecutionResult:
        pass
    @abstractmethod
    def InsertMultiple(self, items: Iterable[Iterable[object]], *columns: str) -> IInsertionQueryExecutionResult:
        pass

class Table(ITable):
    def __init__(self):
        super().__init__()
    
    def Equals(self, item: ITable|object) -> bool:
        return item is self

class IConnection(IDisposable):
    def __init__(self):
        pass

    def Initialize(self) -> None:
        self.Open()
    
    @abstractmethod
    def Open(self) -> bool:
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
    def TryCreateTable(self, name: str, fields: Iterable[IField]) -> ITable:
        pass
    @abstractmethod
    def CreateTable(self, name: str, fields: Iterable[IField]) -> ITable:
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
        
        def GetFields(self) -> IArray[IField]:
            raise GetDisposedError()
        
        def Select(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQueryExecutionResult:
            raise GetDisposedError()
        
        def Insert(self, items: IDictionary[str, object]) -> IInsertionQueryExecutionResult:
            raise GetDisposedError()
        def InsertMultiple(self, items: Iterable[Iterable[object]], *columns: str) -> IInsertionQueryExecutionResult:
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
        
        def GetFields(self) -> IArray[IField]:
            return self.__table.GetFields()
        
        def Select(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQueryExecutionResult|None:
            return self.__table.Select(columns)
        
        def Insert(self, items: IDictionary[str, object]) -> IInsertionQueryExecutionResult:
            return self.__table.Insert(items)
        def InsertMultiple(self, items: Iterable[Iterable[object]], *columns: str) -> IInsertionQueryExecutionResult:
            return self.__table.InsertMultiple(items, *columns)
        
        def Dispose(self) -> None:
            if self.__tableList is None:
                return
            
            self.__table.Dispose()

            self.__tableList.Remove(self)
            self.__tableList = None
            
            self.__table = Connection._GetNullTable()
    
    @final
    class FactoryDictionary[T](Dictionary[type, T]):
        def __init__(self, dictionary: dict[type, T]|None = None):
            super().__init__(dictionary)
    
    __table: ITable = NullTable()

    __fieldFactories: IDictionary[type[Connection], IFieldFactory] = Dictionary[type[Self], IFieldFactory]()
    __queryFactories: IDictionary[type[Connection], IQueryFactory] = Dictionary[type[Self], IQueryFactory]()

    @staticmethod
    def _GetNullTable() -> ITable:
        return Connection.__table
    
    def __init__(self):
        super().__init__()

        self.__tables: List[Connection.Table] = List[Connection.Table]()
    
    @final
    def __TryGetFactory[T](self, dictionary: IDictionary[type[Connection], T]) -> DualValueNullableInfo[type[Connection], T]:
        t: type[Connection] = type(self)

        return DualValueNullableInfo[type[Connection], T](t, dictionary.TryGetAt(t, None))
    
    @abstractmethod
    def _GetFieldFactory(self) -> IFieldFactory:
        pass
    @abstractmethod
    def _GetQueryFactory(self) -> IQueryFactory:
        pass

    @final
    def GetFieldFactory(self) -> IFieldFactory:
        result: DualValueNullableInfo[type[Connection], IFieldFactory|None] = self.__TryGetFactory(Connection.__fieldFactories)

        factory: IFieldFactory|None = result.GetValue()

        if factory is None:
            Connection.__fieldFactories.Add(result.GetKey(), factory := self._GetFieldFactory())
        
        return factory
    @final
    def GetQueryFactory(self) -> IQueryFactory:
        result: DualValueNullableInfo[type[Connection], IQueryFactory|None] = self.__TryGetFactory(Connection.__queryFactories)

        factory: IQueryFactory|None = result.GetValue()

        if factory is None:
            Connection.__queryFactories.Add(result.GetKey(), factory := self._GetQueryFactory())
        
        return factory
    
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
    def _TryCreateTableOverride(self, name: str, fields: Iterable[IField]) -> ITable|None:
        pass
    @abstractmethod
    def _CreateTableOverride(self, name: str, fields: Iterable[IField]) -> ITable:
        pass

    @final
    def TryCreateTable(self, name: str, fields: Iterable[IField]) -> ITable:
        table: ITable|None = self._TryCreateTableOverride(name, fields)
        
        return self.__AddTable(name) if table is None else self.__AddNewTable(table)
    @final
    def CreateTable(self, name: str, fields: Iterable[IField]) -> ITable:
        return self.__AddNewTable(self._CreateTableOverride(name, fields))
    
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