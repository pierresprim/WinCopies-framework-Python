from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import final

import sqlite3

from WinCopies import String, Abstract
from WinCopies.Collections import Enumeration
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IEnumerator, Enumerable, TryAsIterable
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Util import MakeList
from WinCopies.Typing.Object import IString
from WinCopies.Typing.Delegate import Action, Method, IFunction, ValueFunctionUpdater, GetDefaultFunction

from WinCopies.Data import QueryErrorKinds
from WinCopies.Data.Factory import QueryFactory as QueryFactoryBase
from WinCopies.Data.Misc import ITableNameFormater
from WinCopies.Data.Parameter import IFormattable
from WinCopies.Data.Query import (ISelectionQuery, IInsertionQuery, IMultiInsertionQuery, IUpdateQuery,
                                  SelectionQuery as SelectionQueryBase, InsertionQuery as InsertionQueryBase, MultiInsertionQuery as MultiInsertionQueryBase, UpdateQuery as UpdateQueryBase,
                                  InsertionQueryStatementProvider,
                                  ISelectionQueryExecutionResult, IInsertionQueryExecutionResult,
                                  QueryExceptionMapper as QueryExceptionMapperBase)
from WinCopies.Data.QueryBuilder import QueryResult
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet

class QueryExceptionMapper(QueryExceptionMapperBase):
    def __init__(self) -> None: super().__init__()
    
    def _TryMapException(self, exception: Exception) -> QueryErrorKinds:
        return QueryErrorKinds.ParameterLimitExceeded if isinstance(exception, sqlite3.OperationalError) and "too many sql variables" in str(exception).lower() else QueryErrorKinds.Null

class QueryResultBase(Abstract):
    def __init__(self, connection: sqlite3.Connection, query: QueryResult) -> None:
        super().__init__()
        
        self.__cursor: sqlite3.Cursor = self.__ExecuteQuery(connection, query)
    
    @final
    def __ExecuteQuery(self, connection: sqlite3.Connection, query: QueryResult) -> sqlite3.Cursor:
        return connection.execute(query.GetKey(), MakeList(TryAsIterable(query.GetValue())))
    
    @final
    def _GetCursor(self) -> sqlite3.Cursor:
        return self.__cursor
    
    @final
    def GetRowCount(self) -> int:
        return self._GetCursor().rowcount
    
    def Dispose(self) -> None:
        self._GetCursor().close()

class __Query(QueryExceptionMapper, ITableNameFormater):
    def __init__(self) -> None: super().__init__()
    
    @final
    def FormatTableName(self, name: str) -> str: return String.DoubleQuoteSurround(name)

@final
class _ExecutionResult(QueryResultBase, Enumerable[Sequence[object]], ISelectionQueryExecutionResult, IEnumerable[Sequence[object]]):
    @final
    class _Enumerator(Enumeration.Iterator[Sequence[object]]):
        def __init__(self, cursor: sqlite3.Cursor, enumeratorUpdater: Action) -> None:
            super().__init__(cursor)

            self.__enumeratorUpdater: Action = enumeratorUpdater
        
        def _OnEnded(self) -> None: self.__enumeratorUpdater()
    
    @final
    class _FunctionUpdater(ValueFunctionUpdater[IEnumerator[Sequence[object]]|None]):
        def __init__(self, cursor: sqlite3.Cursor, updater: Method[IFunction[IEnumerator[Sequence[object]]|None]], enumeratorUpdater: Action) -> None:
            super().__init__(updater)

            self.__cursor: sqlite3.Cursor = cursor
            self.__enumeratorUpdater: Action = enumeratorUpdater
        
        def _GetValue(self) -> IEnumerator[Sequence[object]]: return _ExecutionResult._Enumerator(self.__cursor, self.__enumeratorUpdater)
    
    def __init__(self, connection: sqlite3.Connection, query: QueryResult) -> None:
        def updateFunction(func: IFunction[IEnumerator[Sequence[object]]|None]) -> None: self.__function = func
        def resetFunction() -> None: self.__function = GetDefaultFunction()
        
        super().__init__(connection, query)

        self.__function = _ExecutionResult._FunctionUpdater(self._GetCursor(), updateFunction, resetFunction)
    
    def TryGetEnumerator(self) -> IEnumerator[Sequence[object]]|None: return self.__function.GetValue()
@final
class _SelectionQuery(SelectionQueryBase, __Query):
    def __init__(self, connection: sqlite3.Connection, tables: ITableParameterSet|str, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None) -> None:
        super().__init__(tables, columns, conditions)

        self.__connection: sqlite3.Connection = connection
    
    def _Validate(self) -> str|None:
        return "There must be at most one table." if self.GetTables().GetCount() > 1 else None
    
    def _Execute(self) -> ISelectionQueryExecutionResult|None:
        query: QueryResult|None = self.GetQuery()

        return None if query is None else _ExecutionResult(self.__connection, query)

@final
class _InsertionQueryExecutionResult(QueryResultBase, IInsertionQueryExecutionResult):
    def __init__(self, cursor: sqlite3.Connection, query: QueryResult) -> None: super().__init__(cursor, query)
    
    def GetLastRowId(self) -> int: return self._GetCursor().lastrowid # type: ignore

class __InsertionQuery(__Query, InsertionQueryStatementProvider):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _GetStatement(self, ignoreExisting: bool = False) -> str: return InsertionQueryBase.GetStandardStatement(ignoreExisting)

@final
class _InsertionQuery(InsertionQueryBase, __InsertionQuery):
    def __init__(self, connection: sqlite3.Connection, tableName: str, items: IDictionary[IString, object], ignoreExisting: bool = False) -> None:
        super().__init__(tableName, items, ignoreExisting)

        self.__connection = connection
    
    def _Validate(self) -> str|None:
        pass
    
    def _Execute(self) -> IInsertionQueryExecutionResult:
        return _InsertionQueryExecutionResult(self.__connection, self.GetQuery())
@final
class _MultiInsertionQuery(MultiInsertionQueryBase, __InsertionQuery):
    def __init__(self, connection: sqlite3.Connection, tableName: str, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> None:
        super().__init__(tableName, columns, items, ignoreExisting)

        self.__connection = connection
    
    def _Validate(self) -> str|None:
        pass
    
    def _Execute(self) -> IInsertionQueryExecutionResult:
        return _InsertionQueryExecutionResult(self.__connection, self.GetQuery())
@final
class _UpdateQuery(UpdateQueryBase, __Query):
    def __init__(self, connection: sqlite3.Connection, tableName: str, values: IDictionary[IString, object], conditions: IConditionParameterSet) -> None:
        super().__init__(tableName, values, conditions)

        self.__connection = connection
    
    def _Validate(self) -> str|None:
        pass
    
    def _Execute(self) -> IInsertionQueryExecutionResult:
        return _InsertionQueryExecutionResult(self.__connection, self.GetQuery())

@final
class Factory(QueryFactoryBase):
    def __init__(self, connection: sqlite3.Connection) -> None:
        super().__init__()

        self.__connection: sqlite3.Connection = connection
    
    def GetSelectionQuery(self, tables: ITableParameterSet|str, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None = None) -> ISelectionQuery: return _SelectionQuery(self.__connection, tables, columns, conditions)
    
    def GetInsertionQuery(self, tableName: str, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery: return _InsertionQuery(self.__connection, tableName, items, ignoreExisting)
    def GetMultiInsertionQuery(self, tableName: str, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery: return _MultiInsertionQuery(self.__connection, tableName, columns, items, ignoreExisting)
    
    def GetUpdateQuery(self, tableName: str, values: IDictionary[IString, object], conditions: IConditionParameterSet) -> IUpdateQuery: return _UpdateQuery(self.__connection, tableName, values, conditions)