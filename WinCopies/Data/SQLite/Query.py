from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import final

import sqlite3

from WinCopies import String
from WinCopies.Collections import Enumeration, CreateList
from WinCopies.Collections.Abstraction import Iterable
from WinCopies.Collections.Enumeration import IIterable, ICountableIterable
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Typing import IInterface
from WinCopies.Typing.Delegate import Action, Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Delegate.Extensions import GetDefaultFunction
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

from WinCopies.Data import Query
from WinCopies.Data.Query import QueryResult, ISelectionQueryExecutionResult, IInsertionQueryExecutionResult
from WinCopies.Data.Misc import ITableNameFormater
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet

class QueryResultBase(IInterface):
    def __init__(self, connection: sqlite3.Connection, query: QueryResult):
        self.__cursor: sqlite3.Cursor = self.__ExecuteQuery(connection, query)
    
    @final
    def __ExecuteQuery(self, connection: sqlite3.Connection, query: QueryResult) -> sqlite3.Cursor:
        def getArguments(args: ICountableIterable[object]|None) -> list[object]:
            if args is None:
                return []
            
            l: list[object] = CreateList(args.GetCount())
            i: int = 0

            for arg in args:
                l[i] = arg

                i += 1
            
            return l
        
        return connection.execute(query.GetKey(), getArguments(query.GetValue()))
    
    @final
    def _GetCursor(self) -> sqlite3.Cursor:
        return self.__cursor
    
    @final
    def GetRowCount(self) -> int:
        return self._GetCursor().rowcount
    
    def Dispose(self) -> None:
        self._GetCursor().close()

class __IQuery(ITableNameFormater):
    def __init__(self):
        super().__init__()
    
    @final
    def FormatTableName(self, tableName: str) -> str:
        return String.DoubleQuoteSurround(tableName)

@final
class SelectionQuery(Query.SelectionQuery, __IQuery):
    @final
    class ExecutionResult(QueryResultBase, ISelectionQueryExecutionResult, IIterable[Sequence[object]]):
        @final
        class Enumerator(Enumeration.Iterator[Sequence[object]]):
            def __init__(self, cursor: sqlite3.Cursor, enumeratorUpdater: Action):
                EnsureDirectModuleCall()

                super().__init__(cursor)

                self.__enumeratorUpdater: Action = enumeratorUpdater
            
            def _OnEnded(self) -> None:
                self.__enumeratorUpdater()
        
        @final
        class FunctionUpdater(ValueFunctionUpdater[Iterator[Sequence[object]]|None]):
            def __init__(self, cursor: sqlite3.Cursor, updater: Method[IFunction[Iterator[Sequence[object]]|None]], enumeratorUpdater: Action):
                super().__init__(updater)

                self.__cursor: sqlite3.Cursor = cursor
                self.__enumeratorUpdater: Action = enumeratorUpdater
            
            def _GetValue(self) -> Iterator[Sequence[object]]:
                return SelectionQuery.ExecutionResult.Enumerator(self.__cursor, self.__enumeratorUpdater)
        
        def __init__(self, connection: sqlite3.Connection, query: QueryResult):
            EnsureDirectModuleCall()

            super().__init__(connection, query)

            self.__function: IFunction[Iterator[Sequence[object]]|None]

            def updateFunction(func: IFunction[Iterator[Sequence[object]]|None]) -> None:
                self.__function = func
            def resetFunction() -> None:
                self.__function = GetDefaultFunction()

            self.__function = SelectionQuery.ExecutionResult.FunctionUpdater(self._GetCursor(), updateFunction, resetFunction)
        
        def TryGetIterator(self) -> Iterator[Sequence[object]]|None:
            return self.__function.GetValue()
    
    def __init__(self, connection: sqlite3.Connection, tables: ITableParameterSet, columns: IColumnParameterSet[IParameter[object]], conditions: IConditionParameterSet|None):
        super().__init__(tables, columns, conditions)

        self.__connection: sqlite3.Connection = connection
    
    def _Validate(self) -> str|None:
        return "There must be at most one table." if self.GetTables().GetCount() > 1 else None
    
    def Execute(self) -> ISelectionQueryExecutionResult|None:
        query: QueryResult|None = self.GetQuery()

        return None if query is None else SelectionQuery.ExecutionResult(self.__connection, query)

@final
class _InsertionQueryExecutionResult(QueryResultBase, IInsertionQueryExecutionResult):
    def __init__(self, cursor: sqlite3.Connection, query: QueryResult):
        EnsureDirectModuleCall()

        super().__init__(cursor, query)
    
    def GetLastRowId(self) -> int:
        return self._GetCursor().lastrowid # type: ignore

@final
class InsertionQuery(Query.InsertionQuery, __IQuery):
    def __init__(self, connection: sqlite3.Connection, tableName: str, items: IDictionary[str, object]):
        super().__init__(tableName, items)

        self.__connection = connection
    
    def Execute(self) -> IInsertionQueryExecutionResult:
        return _InsertionQueryExecutionResult(self.__connection, self.GetQuery())
@final
class MultiInsertionQuery(Query.MultiInsertionQuery, __IQuery):
    def __init__(self, connection: sqlite3.Connection, tableName: str, columns: Sequence[str], items: Iterable[Iterable]):
        super().__init__(tableName, columns, items)

        self.__connection = connection
    
    def Execute(self) -> IInsertionQueryExecutionResult:
        return _InsertionQueryExecutionResult(self.__connection, self.GetQuery())