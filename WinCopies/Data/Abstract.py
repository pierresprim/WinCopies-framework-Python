from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final, NoReturn



from WinCopies import IInterface, IDisposable, Abstract

from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction.Collection import List
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IteratorProvider
from WinCopies.Collections.Extensions import IArray, IList, IDictionary, IReadOnlyKeyedSet
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Iteration import GetFirstItem, SelectWhereNotNone
from WinCopies.Collections.Iteration.AdaptiveRefinement import IAdaptiveRefinement, CreateFineRefinement
from WinCopies.Collections.Iteration.Batch import ResumeResult, ICursor, IHandler, ICompletionHandler

from WinCopies.Delegates import BoolFalse

from WinCopies.Typing import INullable, InvalidOperationError, GetDisposedError
from WinCopies.Typing.Comparison import IEquatable, INotHashableValue
from WinCopies.Typing.Delegate import Method, Function, NullableConverter, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Object import IString
from WinCopies.Typing.Pairing import DualValueBool, CreateDualValueBool
from WinCopies.Typing.Reflection import EnsureDirectModuleCall



from WinCopies.Data import QueryErrorKinds, QueryError, GetActiveTransactionError
from WinCopies.Data.Factory import IFieldFactory, IQueryFactory, ITableQueryFactory, IIndexFactory
from WinCopies.Data.Field import IField
from WinCopies.Data.Index import IIndex
from WinCopies.Data.Parameter import IFormattable
from WinCopies.Data.Query import IQueryLimits, IMutableQueryLimits, ISelectionQuery, IInsertionQuery, IMultiInsertionQuery, IUpdateQuery, ISelectionQueryExecutionResult, IInsertionQueryExecutionResult
from WinCopies.Data.Set import IColumnParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet

@final
class _CompletionHandler(Abstract, ICompletionHandler):
    def __init__(self, pkCount: int, limits: IMutableQueryLimits) -> None:
        super().__init__()

        self.__pkCount: int = pkCount
        self.__limits:  IMutableQueryLimits = limits

    def OnCompleted(self, size: int|None, safe: bool) -> None:
        if size is not None: self.__limits.UpdateParameterCount(size * self.__pkCount, safe)

class ISelectionHandler(IHandler):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryResume(self, newSize: int|None = None) -> ResumeResult|None:
        ...
@final
class _SelectionHandler(Abstract, ISelectionHandler):
    def __init__(self, refine: bool, pkCount: int, limits: IMutableQueryLimits) -> None:
        super().__init__()

        self.__refine: bool = refine
        self.__cursor: ICursor|None = None
        self.__completionHandler: ICompletionHandler = _CompletionHandler(pkCount, limits)

    def Initialize(self, cursor: ICursor) -> None: self.__cursor = cursor

    def CreateAdaptiveRefinement(self, size: int) -> IAdaptiveRefinement: return CreateFineRefinement(size, self.__refine)

    def GetCompletionHandler(self) -> ICompletionHandler: return self.__completionHandler
    
    def TryResume(self, newSize: int|None = None) -> ResumeResult|None:
        cursor: ICursor|None = self.__cursor

        return None if cursor is None else cursor.TryResume(newSize)

class _ITransactionCheckable(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _CheckIfActiveTransaction(self) -> bool:
        ...
    @final
    def _EnsureNoActiveTransaction(self) -> None:
        if self._CheckIfActiveTransaction(): raise InvalidOperationError("DDL is not allowed while a transaction is active.")

class ITable(IEquatable['ITable'], IRemovable, IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetName(self) -> str:
        ...
    @abstractmethod
    def SetName(self, name: str) -> None:
        ...

    @abstractmethod
    def GetFields(self) -> IArray[IField]:
        ...

    @abstractmethod
    def GetIndices(self) -> IArray[IIndex]:
        ...

    @abstractmethod
    def GetQueryFactory(self) -> ITableQueryFactory:
        ...

    @final
    def Select(self, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None = None) -> ISelectionQueryExecutionResult|None:
        return self.GetQueryFactory().GetSelectionQuery(columns, conditions).Execute()
    @abstractmethod
    def SelectByKeys(self, columns: IColumnParameterSet[IFormattable], keys: IReadOnlyKeyedSet[IString, object]) -> Generator[ISelectionQueryExecutionResult]|None:
        ...
    
    @abstractmethod
    def Insert(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult:
        ...
    @abstractmethod
    def InsertMany(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult:
        ...
    
    @abstractmethod
    def Update(self, values: IDictionary[IString, object], conditions: IConditionParameterSet) -> IInsertionQueryExecutionResult:
        ...
    
    @abstractmethod
    def TryRemove(self) -> bool:
        ...
class Table(Abstract, ITable, INotHashableValue, _ITransactionCheckable):
    class _QueryFactory(Abstract, ITableQueryFactory):
        def __init__(self, table: Table) -> None:
            super().__init__()

            self.__table: Table = table
            self.__factory: IQueryFactory = table._GetConnection().GetFactoryProvider().GetQueryFactory()
        
        @final
        def _GetTable(self) -> Table:
            return self.__table
        @final
        def _GetFactory(self) -> IQueryFactory:
            return self.__factory
        
        @final
        def _GetTableName(self) -> str:
            return self._GetTable().GetName()
        
        @final
        def TryBuildConditionsByKeys(self, keys: IReadOnlyKeyedSet[IString, object], maxParameterCount: int|None = None, handler: IHandler|None = None) -> Generator[IConditionParameterSet]|None: return self._GetFactory().TryBuildConditionsByKeys(keys, maxParameterCount, handler)

        @final
        def GetSelectionQuery(self, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None = None) -> ISelectionQuery: return self._GetFactory().GetSelectionQuery(self._GetTableName(), columns, conditions)

        @final
        def GetInsertionQuery(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery: return self._GetFactory().GetInsertionQuery(self._GetTableName(), items, ignoreExisting)
        @final
        def GetMultiInsertionQuery(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery: return self._GetFactory().GetMultiInsertionQuery(self._GetTableName(), columns, items, ignoreExisting)
        
        @final
        def GetUpdateQuery(self, values: IDictionary[IString, object], conditions: IConditionParameterSet) -> IUpdateQuery: return self._GetFactory().GetUpdateQuery(self._GetTableName(), values, conditions)
    
    def __init__(self) -> None:
        super().__init__()

        self.__queryFactory: ITableQueryFactory|None = None
    
    @final
    def _EnsureActiveTransaction(self) -> None:
        if not self._CheckIfActiveTransaction(): raise InvalidOperationError("DML requires an active transaction.")
    
    @abstractmethod
    def _GetConnection(self) -> IConnection:
        ...
    
    @abstractmethod
    def _GetQueryLimits(self) -> IMutableQueryLimits:
        ...
    
    @final
    def GetQueryFactory(self) -> ITableQueryFactory:
        if self.__queryFactory is None: self.__queryFactory = Table._QueryFactory(self)
        
        return self.__queryFactory
    
    @final
    def _CheckIfActiveTransaction(self) -> bool:
        return self._GetConnection().CheckIfActiveTransaction()
    
    @final
    def SelectByKeys(self, columns: IColumnParameterSet[IFormattable], keys: IReadOnlyKeyedSet[IString, object]) -> Generator[ISelectionQueryExecutionResult]|None:
        def setConditions(conditionSet: IConditionParameterSet) -> None: query.SetConditions(conditionSet)

        def _select(conditionSet: IConditionParameterSet) -> ISelectionQueryExecutionResult|None:
            setConditions(conditionSet)

            return query.Execute()
        def select(conditionSet: IConditionParameterSet, handler: ISelectionHandler) -> ISelectionQueryExecutionResult|None:
            def throw(msg: str) -> NoReturn: raise InvalidOperationError(msg)

            setConditions(conditionSet)

            result: ISelectionQueryExecutionResult|QueryErrorKinds|None = query.Execute(QueryErrorKinds.ParameterLimitExceeded)

            if isinstance(result, QueryErrorKinds):
                if result == QueryErrorKinds.ParameterLimitExceeded:
                    resumeResult: ResumeResult|None = handler.TryResume()

                    if resumeResult is None: raise InvalidOperationError(f"{handler.TryResume.__name__} called before handler initialization.")

                    match resumeResult:
                        case ResumeResult.Resumed: return None
                        
                        case ResumeResult.AtFloor|ResumeResult.Exhausted: raise QueryError(QueryErrorKinds.ParameterLimitExceeded)
                        
                        case ResumeResult.PostConvergence: throw("Resume failed at a size previously proven valid (limit shifted).")
                        case ResumeResult.ResumeFailed: throw("Enumerator failed to re-arm after a valid refinement.")
                        case ResumeResult.NotResumable: throw("Cursor is not in a resumable state.")
                
                raise InvalidOperationError("An unexpected error occurred.")

            return result
        
        def getLimit() -> tuple[int|None, ISelectionHandler|None, NullableConverter[IConditionParameterSet, ISelectionQueryExecutionResult]]:
            limit: DualValueBool[int]|None = queryLimits.GetMaxParameterCount()

            if limit is None: return (None, None, _select)
            
            handler: ISelectionHandler = _SelectionHandler(not limit.GetValue(), keys.GetKeys().GetCount(), queryLimits)
            
            return (limit.GetKey(), handler, lambda conditionSet: select(conditionSet, handler))
        
        if keys.GetCount() < 1: return None

        factory: ITableQueryFactory = self.GetQueryFactory()
        queryLimits: IMutableQueryLimits = self._GetQueryLimits()
        maxParameterCount, handler, selector = getLimit()
        
        conditions: Generator[IConditionParameterSet]|None = factory.TryBuildConditionsByKeys(keys, maxParameterCount, handler)

        if conditions is None: return None
        
        query: ISelectionQuery = factory.GetSelectionQuery(columns)
        
        return SelectWhereNotNone(conditions, selector)
    
    def Equals(self, item: ITable|object) -> bool: return item is self

    @final
    def Insert(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult:
        self._EnsureActiveTransaction()
        
        return self.GetQueryFactory().GetInsertionQuery(items, ignoreExisting).Execute()
    @final
    def InsertMany(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult:
        self._EnsureActiveTransaction()
        
        return self.GetQueryFactory().GetMultiInsertionQuery(columns, items, ignoreExisting).Execute()
    
    @final
    def Update(self, values: IDictionary[IString, object], conditions: IConditionParameterSet) -> IInsertionQueryExecutionResult:
        self._EnsureActiveTransaction()
        
        return self.GetQueryFactory().GetUpdateQuery(values, conditions).Execute()

    @abstractmethod
    def _Remove(self) -> None:
        ...

    @final
    def Remove(self) -> None:
        self._EnsureNoActiveTransaction()

        self._Remove()
    @final
    def TryRemove(self) -> bool:
        if self._CheckIfActiveTransaction(): return False
        
        self._Remove()

        return True

class IFactoryProvider(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetFieldFactory(self) -> IFieldFactory:
        ...
    @abstractmethod
    def GetQueryFactory(self) -> IQueryFactory:
        ...
    @abstractmethod
    def GetIndexFactory(self) -> IIndexFactory:
        ...

class IDataBase(IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetTableNames(self) -> Iterable[str]:
        ...

    @abstractmethod
    def TryGetTable(self, name: str) -> ITable|None:
        ...
    
    @abstractmethod
    def EnumerateTables(self) -> Generator[ITable]:
        ...
    @abstractmethod
    def GetTables(self) -> IEnumerable[ITable]:
        ...

    @abstractmethod
    def TryCreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable|None:
        ...
    @abstractmethod
    def CreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable:
        ...

@final
class _NullTable(Abstract, ITable):
    def __init__(self) -> None: super().__init__()
    
    def Equals(self, item: ITable|object) -> bool: return item is self or isinstance(item, ITable)
    
    def GetName(self) -> str: raise GetDisposedError()
    def SetName(self, name: str) -> None: raise GetDisposedError()

    def GetQueryFactory(self) -> ITableQueryFactory: raise GetDisposedError()
    
    def GetFields(self) -> IArray[IField]: raise GetDisposedError()

    def GetIndices(self) -> IArray[IIndex]: raise GetDisposedError()
    
    def SelectByKeys(self, columns: IColumnParameterSet[IFormattable], keys: IReadOnlyKeyedSet[IString, object]) -> Generator[ISelectionQueryExecutionResult]|None: raise GetDisposedError()

    def Insert(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult: raise GetDisposedError()
    def InsertMany(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult: raise GetDisposedError()

    def Update(self, values: IDictionary[IString, object], conditions: IConditionParameterSet | None) -> IInsertionQueryExecutionResult: raise GetDisposedError()
    
    def Remove(self) -> None: raise GetDisposedError()
    def TryRemove(self) -> bool: return False
    
    def Dispose(self) -> None: pass
class _TableBase(Abstract, ITable):
    def __init__(self, tables: IList[_TableBase], table: ITable) -> None:
        EnsureDirectModuleCall()

        super().__init__()
        
        self.__tables: IList[_TableBase]|None = tables
        self.__table: ITable = table

    @abstractmethod
    def _GetNullTable(self) -> ITable:
        ...
    
    @final
    def Equals(self, item: ITable|object) -> bool: return isinstance(item, _TableBase) and self.__tables == item.__tables and self.GetName() == item.GetName()
    
    @final
    def GetName(self) -> str: return self.__table.GetName()
    @final
    def SetName(self, name: str) -> None: self.__table.SetName(name)

    @final
    def GetQueryFactory(self) -> ITableQueryFactory: return self.__table.GetQueryFactory()

    @final
    def GetIndices(self) -> IArray[IIndex]: return self.__table.GetIndices()
    
    @final
    def GetFields(self) -> IArray[IField]: return self.__table.GetFields()
    
    @final
    def SelectByKeys(self, columns: IColumnParameterSet[IFormattable], keys: IReadOnlyKeyedSet[IString, object]) -> Generator[ISelectionQueryExecutionResult]|None: return self.__table.SelectByKeys(columns, keys)

    @final
    def Insert(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult: return self.__table.Insert(items, ignoreExisting)
    @final
    def InsertMany(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IInsertionQueryExecutionResult: return self.__table.InsertMany(columns, items, ignoreExisting)

    @final
    def Update(self, values: IDictionary[IString, object], conditions: IConditionParameterSet) -> IInsertionQueryExecutionResult: return self.__table.Update(values, conditions)
    
    @final
    def Remove(self) -> None: self.__table.Remove()
    @final
    def TryRemove(self) -> bool: return self.__table.TryRemove()
    
    @final
    def Dispose(self) -> None:
        tables: IList[_TableBase]|None = self.__tables

        if tables is None: return
        
        self.__table.Dispose()

        tables.Remove(self)
        self.__tables = None
        
        self.__table = self._GetNullTable()

class DataBase(Abstract, IDataBase, _ITransactionCheckable):
    @final
    class _Table(_TableBase):
        def __init__(self, tables: IList[_TableBase], table: ITable) -> None: super().__init__(tables, table)

        def _GetNullTable(self) -> ITable: return DataBase._GetNullTable()
    
    __table: ITable = _NullTable()
    
    def __init__(self) -> None:
        super().__init__()

        self.__tables: IList[_TableBase] = List[_TableBase]()
    
    @abstractmethod
    def _GetConnection(self) -> IConnection:
        ...
    
    @final
    def _CheckIfActiveTransaction(self) -> bool: return self._GetConnection().CheckIfActiveTransaction()

    @staticmethod
    def _GetNullTable() -> ITable:
        return DataBase.__table
    
    @abstractmethod
    def _TryCreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> INullable[ITable]|None:
        ...
    @abstractmethod
    def _CreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable:
        ...
    
    @final
    def __AddNewTable(self, table: ITable) -> ITable:
        _table: DataBase._Table = DataBase._Table(self.__tables, table)
        
        self.__tables.Add(_table)

        return _table
    @final
    def __AddTable(self, name: str) -> ITable:
        return self.__AddNewTable(self._GetTable(name))

    @final
    def TryCreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable|None:
        def addTable() -> ITable: return self.__AddTable(name)
        
        def getTable(table: ITable|None) -> ITable: return addTable() if table is None else self.__AddNewTable(table)
        def tryGetTable() -> ITable:
            table: ITable|None = self.__TryGetTable(name)

            return addTable() if table is None else table
        
        if self._CheckIfActiveTransaction(): return None
        
        table: INullable[ITable]|None = self._TryCreateTableOverride(name, fields, indices)
        
        return tryGetTable() if table is None else getTable(table.TryGetValue())
    @final
    def CreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None = None) -> ITable:
        self._EnsureNoActiveTransaction()

        return self.__AddNewTable(self._CreateTableOverride(name, fields, indices))
    
    @abstractmethod
    def _GetTable(self, name: str) -> ITable:
        ...

    @final
    def __TryGetTable(self, tableName: str) -> ITable|None:
        return GetFirstItem(self.__tables.AsIterable(), lambda table: table.GetName() == tableName).TryGetValue()
    
    @final
    def TryGetTable(self, name: str) -> ITable|None:
        table: ITable|None = self.__TryGetTable(name)

        return self.__AddTable(name) if table is None and name in self.GetTableNames() else table
    
    @final
    def EnumerateTables(self) -> Generator[ITable]:
        table: ITable|None = None
        
        for name in self.GetTableNames():
            if (table := self.__TryGetTable(name)) is None: table = self.__AddTable(name)
            
            yield table
    @final
    def GetTables(self) -> IEnumerable[ITable]:
        return IteratorProvider[ITable](self.EnumerateTables)
    
    def Dispose(self) -> None:
        tables: IList[_TableBase] = self.__tables

        while tables.HasItems(): tables.GetAt(0).Dispose() # Need a custom iteration because DataBase.__Table.Dispose() removes the table from the cache.

class ITransactionCookie(IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def HasActiveTransaction(self) -> bool:
        ...
    
    @abstractmethod
    def CreateTransactionControl(self) -> ITransactionControl:
        ...
    
    @abstractmethod
    def NotifyTransactionBegan(self, control: ITransactionControl) -> None:
        ...

    @abstractmethod
    def NotifyTransactionEnded(self) -> None:
        ...
class TransactionCookie(Abstract, ITransactionCookie):
    def __init__(self) -> None:
        super().__init__()

        self.__transactionControl: ITransactionControl|None = None
    
    @final
    def HasActiveTransaction(self) -> bool: return self.__transactionControl is not None

    @final
    def NotifyTransactionBegan(self, control: ITransactionControl) -> None:
        if self.HasActiveTransaction(): raise GetActiveTransactionError()

        self.__transactionControl = control

    @final
    def NotifyTransactionEnded(self) -> None: self.__transactionControl = None

    def Dispose(self) -> None:
        transactionControl: ITransactionControl|None = self.__transactionControl

        if transactionControl is None: return

        try: transactionControl.Rollback()
        except Exception: pass
        finally: self.__transactionControl = None

class ITransactionControl(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def IsActive(self) -> bool:
        ...

    @abstractmethod
    def Begin(self) -> bool:
        ...
    
    @abstractmethod
    def Commit(self) -> bool:
        ...
    @abstractmethod
    def Rollback(self) -> bool:
        ...
class TransactionControl(Abstract, ITransactionControl):
    def __init__(self, cookie: ITransactionCookie) -> None:
        def notifyTransactionEnded() -> None: cookie.NotifyTransactionEnded()
        def onEnded() -> None:
            self.__commit = BoolFalse
            self.__rollback = BoolFalse

            notifyTransactionEnded()

        def begin() -> bool:
            cookie.NotifyTransactionBegan(self)

            try:
                self._BeginOverride()

                self.__begin = BoolFalse

                self.__commit = commit
                self.__rollback = rollback

                return True
            
            except BaseException:
                notifyTransactionEnded()
                
                raise
        
        def commit() -> bool:
            self._CommitOverride()

            onEnded()

            return True
        def rollback() -> bool:
            try: self._RollbackOverride()
            finally: onEnded()
            
            return True

        super().__init__()

        self.__begin: Function[bool] = begin # type: ignore[no-redef]

        self.__commit: Function[bool] = BoolFalse # type: ignore[no-redef]
        self.__rollback: Function[bool] = BoolFalse # type: ignore[no-redef]
    
    @final
    def IsActive(self) -> bool: return self.__commit != BoolFalse

    @final
    def Begin(self) -> bool: return self.__begin()

    @final
    def Commit(self) -> bool: return self.__commit()
    @final
    def Rollback(self) -> bool: return self.__rollback()

    @abstractmethod
    def _BeginOverride(self) -> None:
        ...
    
    @abstractmethod
    def _CommitOverride(self) -> None:
        ...
    @abstractmethod
    def _RollbackOverride(self) -> None:
        ...

def GetConnectionClosedError() -> Exception:
    return InvalidOperationError("The connection is closed.")

class _IConnectionData(IDisposable):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetCursor(self) -> IDataBase:
        ...

    @abstractmethod
    def GetTransactionCookie(self) -> ITransactionCookie:
        ...

    @abstractmethod
    def GetFactories(self) -> IFactoryProvider:
        ...
    
    @abstractmethod
    def GetMutableQueryLimits(self) -> IMutableQueryLimits:
        ...
    @abstractmethod
    def GetQueryLimits(self) -> IQueryLimits:
        ...

class IConnection(IDisposable):
    def __init__(self) -> None:
        super().__init__()

    def Initialize(self) -> None: self.Open()
    
    @abstractmethod
    def IsOpen(self) -> bool:
        ...
    @abstractmethod
    def Open(self) -> bool|None:
        ...

    @abstractmethod
    def HasActiveTransaction(self) -> bool|None:
        ...
    @final
    def CheckIfActiveTransaction(self) -> bool:
        return self.HasActiveTransaction() is True
    
    @abstractmethod
    def CreateTransactionControl(self) -> ITransactionControl:
        ...

    @abstractmethod
    def FormatTableName(self, name: str) -> str:
        ...

    @abstractmethod
    def GetQueryLimits(self) -> IQueryLimits:
        ...
    
    @abstractmethod
    def GetCursor(self) -> IDataBase:
        ...
    
    @abstractmethod
    def GetFactoryProvider(self) -> IFactoryProvider:
        ...

    @abstractmethod
    def Close(self) -> None:
        ...

    def Dispose(self) -> None: self.Close()

@final
class _Data(_IConnectionData):
    @final
    class _Factories(Abstract, IFactoryProvider):
        class _Updater[T](ValueFunctionUpdater[T]):
            def __init__(self, provider: IFactoryProvider, updater: Method[IFunction[T]]) -> None:
                super().__init__(updater)

                self.__provider: IFactoryProvider = provider
            
            @final
            def _GetProvider(self) -> IFactoryProvider:
                return self.__provider
        
        @final
        class _Field(_Updater[IFieldFactory]):
            def __init__(self, provider: IFactoryProvider, updater: Method[IFunction[IFieldFactory]]) -> None:
                super().__init__(provider, updater)
            
            def _GetValue(self) -> IFieldFactory: return self._GetProvider().GetFieldFactory()
        @final
        class _Query(_Updater[IQueryFactory]):
            def __init__(self, provider: IFactoryProvider, updater: Method[IFunction[IQueryFactory]]) -> None:
                super().__init__(provider, updater)
            
            def _GetValue(self) -> IQueryFactory: return self._GetProvider().GetQueryFactory()
        @final
        class _Index(_Updater[IIndexFactory]):
            def __init__(self, provider: IFactoryProvider, updater: Method[IFunction[IIndexFactory]]) -> None:
                super().__init__(provider, updater)
            
            def _GetValue(self) -> IIndexFactory: return self._GetProvider().GetIndexFactory()
        
        def __init__(self, provider: IFactoryProvider) -> None:
            def updateField(func: IFunction[IFieldFactory]) -> None: self.__field = func
            def updateQuery(func: IFunction[IQueryFactory]) -> None: self.__query = func
            def updateIndex(func: IFunction[IIndexFactory]) -> None: self.__index = func
            
            super().__init__()

            self.__field: IFunction[IFieldFactory] = _Data._Factories._Field(provider, updateField) # type: ignore[no-redef]
            self.__query: IFunction[IQueryFactory] = _Data._Factories._Query(provider, updateQuery) # type: ignore[no-redef]
            self.__index: IFunction[IIndexFactory] = _Data._Factories._Index(provider, updateIndex) # type: ignore[no-redef]

        @final
        def GetFieldFactory(self) -> IFieldFactory: return self.__field.GetValue()
        @final
        def GetQueryFactory(self) -> IQueryFactory: return self.__query.GetValue()
        @final
        def GetIndexFactory(self) -> IIndexFactory: return self.__index.GetValue()
    
    @final
    class _QueryLimits(Abstract, IQueryLimits):
        def __init__(self, queryLimits: IMutableQueryLimits) -> None:
            super().__init__()

            self.__queryLimits: IMutableQueryLimits = queryLimits

        def GetMaxParameterCount(self) -> DualValueBool[int]|None: return self.__queryLimits.GetMaxParameterCount()

        def GetMaxQuerySize(self) -> int|None: return self.__queryLimits.GetMaxQuerySize()
    
    def __init__(self, cursor: IDataBase, cookie: ITransactionCookie, factories: IFactoryProvider, queryLimits: IMutableQueryLimits) -> None:
        super().__init__()

        self.__cursor: IDataBase = cursor
        self.__cookie: ITransactionCookie = cookie

        self.__factories: IFactoryProvider = _Data._Factories(factories)

        self.__mutableQueryLimits: IMutableQueryLimits = queryLimits
        self.__queryLimits: IQueryLimits = _Data._QueryLimits(queryLimits)
    
    def GetCursor(self) -> IDataBase: return self.__cursor
    
    def GetTransactionCookie(self) -> ITransactionCookie: return self.__cookie
    
    def GetFactories(self) -> IFactoryProvider: return self.__factories
    
    def GetMutableQueryLimits(self) -> IMutableQueryLimits: return self.__mutableQueryLimits
    def GetQueryLimits(self) -> IQueryLimits: return self.__queryLimits
    
    def Dispose(self) -> None:
        self.__cookie.Dispose()
        self.__cursor.Dispose()

@final
class _MutableQueryLimits(Abstract, IMutableQueryLimits):
    def __init__(self, queryLimits: IQueryLimits) -> None:
        super().__init__()

        self.__maxParameterCount: DualValueBool[int]|None = queryLimits.GetMaxParameterCount()
        self.__maxQuerySize: int|None = queryLimits.GetMaxQuerySize()

    def GetMaxParameterCount(self) -> DualValueBool[int]|None: return self.__maxParameterCount

    def GetMaxQuerySize(self) -> int|None: return self.__maxQuerySize
    
    def UpdateParameterCount(self, size: int, safe: bool) -> bool|None:
        def update(result: bool) -> bool:
            self.__maxParameterCount = CreateDualValueBool(size, result)

            return result

        if safe: return update(True)
        
        maxParameterCount: DualValueBool[int]|None = self.__maxParameterCount
        
        return update(False) if maxParameterCount is None or size > maxParameterCount.GetKey() else None

class Connection(Abstract, IConnection):
    
    
    def __init__(self) -> None:
        super().__init__()

        self.__data: _IConnectionData|None = None
    
    @final
    def __GetData(self) -> _IConnectionData:
        data: _IConnectionData|None = self.__data

        if data is None: raise GetConnectionClosedError()
        
        return data
    
    @abstractmethod
    def _CreateTransactionCookie(self) -> ITransactionCookie:
        ...

    @abstractmethod
    def _CreateCursor(self) -> IDataBase:
        ...
    
    @final
    def HasActiveTransaction(self) -> bool|None:
        data: _IConnectionData|None = self.__data
        
        return None if data is None else data.GetTransactionCookie().HasActiveTransaction()
    @final
    def CreateTransactionControl(self) -> ITransactionControl: return self.__GetData().GetTransactionCookie().CreateTransactionControl()
    
    @final
    def IsOpen(self) -> bool: return self.__data is not None
    
    @abstractmethod
    def _Open(self, queryLimits: IMutableQueryLimits) -> bool:
        ...
    @final
    def Open(self) -> bool|None:
        if self.IsOpen(): return None
        
        queryLimits: IMutableQueryLimits = _MutableQueryLimits(self._CreateQueryLimits())

        if self._Open(queryLimits):
            self.__data = _Data(self._CreateCursor(), self._CreateTransactionCookie(), self._CreateFactoryProvider(), queryLimits)

            return True
        
        return False
    
    @abstractmethod
    def _CreateFactoryProvider(self) -> IFactoryProvider:
        ...
    @final
    def GetFactoryProvider(self) -> IFactoryProvider: return self.__GetData().GetFactories()

    @final
    def GetCursor(self) -> IDataBase: return self.__GetData().GetCursor()
    
    @abstractmethod
    def _CreateQueryLimits(self) -> IQueryLimits:
        ...
    
    @final
    def _GetMutableQueryLimits(self) -> IMutableQueryLimits:
        return self.__GetData().GetMutableQueryLimits()
    @final
    def GetQueryLimits(self) -> IQueryLimits: return self.__GetData().GetQueryLimits()
    
    @abstractmethod
    def _CloseOverride(self) -> None:
        ...
    
    @final
    def Close(self) -> None:
        data: _IConnectionData|None = self.__data

        if data is None: return
        
        data.Dispose()
        self.__data = None
        
        self._CloseOverride()