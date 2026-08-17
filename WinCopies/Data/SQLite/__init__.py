from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import auto, Enum, Flag
from typing import final, Callable

import sqlite3



from WinCopies import IDisposable, Abstract, TryConvertToInt

from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction.Collection import Array
from WinCopies.Collections.Abstraction.Mapping import Dictionary
from WinCopies.Collections.Extensions import IArray
from WinCopies.Collections.Iteration import Append, Select, EnsureOnlyOne
from WinCopies.Collections.Linked.Singly import IList, Queue

from WinCopies.Enum import HasFlag

from WinCopies.String import DoubleQuoteSurround

from WinCopies.Typing import DiscardReason, IRevocableInfo, INullable, Disposable, GetDiscardedError
from WinCopies.Typing.Delegate import Function, IFunction, IStruct, Struct
from WinCopies.Typing.Pairing import DualValueBool, DualValueNullableInfo, CreateDualResult, CreateDualValueBool, CreateDualValueNullableInfo



from WinCopies.Data import IOperand, IColumn, Column, TableColumn, Operator
from WinCopies.Data.Abstract import IFactoryProvider, IConnection, ITransactionCookie, ITransactionControl, IDataBase, ITable, Connection as ConnectionBase, TransactionCookie, TransactionControl, DataBase as DataBaseAbstract, Table
from WinCopies.Data.Extensions import GetField
from WinCopies.Data.Factory import IFieldFactory, IQueryFactory, IIndexFactory
from WinCopies.Data.Field import FieldType, FieldAttributes, IntegerMode, RealMode, TextMode, IField
from WinCopies.Data.Index import IndexKind, IIndex
from WinCopies.Data.Misc import JoinType
from WinCopies.Data.Parameter import IFormattable, IParameter, ColumnParameter, TableParameter, MakeTableColumnIterable, MakeTableValueIterable, GetNullFieldParameter, GetNotNullFieldParameter, CreateFieldParameterFromValue
from WinCopies.Data.Query import IMutableQueryLimits, IQueryLimits, ISelectionQuery, ISelectionQueryExecutionResult
from WinCopies.Data.Set.Extensions import Join, ColumnParameterSet, TableParameterSet, ConditionSet, ExistenceSet, IExistenceQuery, ExistenceQuery, MakeColumnParameterSet, MakeConjunctionSet

from WinCopies.Data.SQLite.Factory import FieldFactory, IndexFactory
from WinCopies.Data.SQLite.Query import Factory

@final
class _Connection(Disposable):
    def __init__(self, connection: Connection, innerCollection: sqlite3.Connection, queryLimits: IMutableQueryLimits) -> None:
        super().__init__()

        self.__connection: IConnection|None = connection
        self.__innerConnection: sqlite3.Connection|None = innerCollection

        self.__queryLimits: IMutableQueryLimits = queryLimits
    
    def GetConnection(self) -> IConnection:
        connection: IConnection|None = self.__connection

        if connection is None: raise GetDiscardedError()
        
        return connection
    
    def GetInnerConnection(self) -> sqlite3.Connection:
        innerConnection: sqlite3.Connection|None = self.__innerConnection

        if innerConnection is None: raise GetDiscardedError()
        
        return innerConnection
    
    def GetQueryLimits(self) -> IMutableQueryLimits:
        return self.__queryLimits

    def _OnDisposing(self, reason: DiscardReason) -> None:
        super()._OnDisposing(reason)

        self.GetInnerConnection().close()
    
    def _DisposeOverride(self, reason: DiscardReason) -> None:
        super()._DisposeOverride(reason)
        
        self.__innerConnection = None
        self.__connection = None

@final
class _Table(Table):
    @final
    class __Connection(Abstract, IDisposable):
        def __init__(self, connection: _Connection) -> None: self.__connection: _Connection|None = connection
        
        def __GetConnection(self) -> _Connection:
            connection: _Connection|None = self.__connection

            if connection is None: raise GetDiscardedError()
            
            return connection
        
        def GetConnection(self) -> IConnection:
            return self.__GetConnection().GetConnection()
        
        def GetQueryLimits(self) -> IMutableQueryLimits:
            return self.__GetConnection().GetQueryLimits()
        
        def Execute(self, sql: str, values: Sequence[object]|None = None) -> None:
            connection: sqlite3.Connection = self.__GetConnection().GetInnerConnection()

            if values is None: connection.execute(sql)
            else: connection.execute(sql, values)
        
        def Dispose(self) -> None: self.__connection = None
    
    class FieldAttributes(Flag):
        Null = 0
        Integer = auto()
        PrimaryKey = auto()
        NoDefault = auto()
        Unique = auto()
        Nullable = auto()
    
    def __init__(self, connection: _Connection, name: str) -> None:
        super().__init__()
        
        self.__connection: _Table.__Connection = _Table.__Connection(connection)
        self.__factoryProvider: IFactoryProvider = self._GetConnection().GetFactoryProvider()

        self.__name: str = name
        self.__fields: IArray[IField]|None = None
        self.__indices: IArray[IIndex]|None = None
    
    def __GetQueryFactory(self) -> IQueryFactory:
        return self.__factoryProvider.GetQueryFactory()
    
    def __GetArray[T](self, func: Function[Iterable[T]]) -> IArray[T]:
        return Array[T](func())
    
    def _GetConnection(self) -> IConnection: return self.__connection.GetConnection()
    
    def _GetQueryLimits(self) -> IMutableQueryLimits: return self.__connection.GetQueryLimits()
    
    def GetName(self) -> str: return self.__name
    def SetName(self, name: str) -> None:
        connection: IConnection = self._GetConnection()

        self.__connection.Execute(f"ALTER TABLE {connection.FormatTableName(self.GetName())} RENAME TO {connection.FormatTableName(name)}")
    
    def GetFields(self) -> IArray[IField]:
        def getFields() -> Generator[IField]:
            def getFieldType(fieldType: str) -> DualValueNullableInfo[FieldType, Enum]:
                def getResult(fieldType: FieldType, fieldMode: Enum|None) -> DualValueNullableInfo[FieldType, Enum]: return CreateDualValueNullableInfo(fieldType, fieldMode)
                
                match fieldType.upper():
                    case "INTEGER" | "INT": return getResult(FieldType.Integer, IntegerMode.Long)
                    case "REAL" | "FLOAT" | "DOUBLE": return getResult(FieldType.Real, RealMode.Double)
                    
                    case "TEXT" | "VAR" | "VARCHAR": return getResult(FieldType.Text, TextMode.Text)
                    
                    case '': return getResult(FieldType.Null, None)
                    
                    case _: raise NotImplementedError(f"The '{fieldType}' field type is not supported.")
            
            def getAttributes(attributes: _Table.FieldAttributes) -> FieldAttributes:
                def check(value: _Table.FieldAttributes) -> bool: return HasFlag(attributes, value)
                
                if attributes == _Table.FieldAttributes.Null: return FieldAttributes.Null
                
                result: FieldAttributes = FieldAttributes.Null
                
                if check(_Table.FieldAttributes.PrimaryKey):
                    result = FieldAttributes.PrimaryKey
                    
                    if check(_Table.FieldAttributes.Integer) and check(_Table.FieldAttributes.NoDefault): result |= FieldAttributes.AutoIncrement
                
                if check(_Table.FieldAttributes.Unique): result |= FieldAttributes.Unique
                if check(_Table.FieldAttributes.Nullable): result |= FieldAttributes.Nullable
                
                return result
            
            def checkAttributeValue(row: Sequence[object], index: int) -> bool:
                value: int|None = TryConvertToInt(row[index])

                return not (value is None or value <= 0)
            
            def executeQuery() -> ISelectionQueryExecutionResult|None:
                query: ISelectionQuery = self.__GetQueryFactory().GetSelectionQuery(
                    TableParameterSet({
                        "PRAGMA_TABLE_INFO": TableParameter[str](
                            't', MakeTableValueIterable(self.GetName()))}),
                    ColumnParameterSet[IFormattable]({
                        Column("name"): None,
                        Column("type"): None,
                        Column("pk"): None,
                        Column("dflt_value"): GetNullFieldParameter(),
                        Column("notnull"): CreateFieldParameterFromValue(Operator.LessThanOrEquals, 0)}))
                
                uniqueFlagQuery: IExistenceQuery = ExistenceQuery(
                    "PRAGMA_INDEX_LIST",
                    TableParameter[str](
                        'i',
                        MakeTableValueIterable(self.GetName())),
                    MakeConjunctionSet(
                        CreateDualResult(TableColumn('i', "unique"), CreateFieldParameterFromValue(Operator.Equals, 1))))
                uniqueFlagQuery.SetJoinsFromValues(
                    Join(
                        JoinType.Inner,
                        "PRAGMA_INDEX_INFO",
                        TableParameter[IColumn](
                            "info",
                            MakeTableColumnIterable(
                                TableColumn('i', "name"))),
                        MakeConjunctionSet(
                            CreateDualResult(TableColumn("info", "cid"), ColumnParameter.CreateForTableColumn(Operator.Equals, 't', "cid")))))

                query.GetCases().Add(ExistenceSet("isUnique", uniqueFlagQuery))

                return query.Execute()

            columns: ISelectionQueryExecutionResult|None = executeQuery()

            if columns is None: return
            
            fieldFactory: IFieldFactory = self.__factoryProvider.GetFieldFactory()
            attributes: _Table.FieldAttributes|None = None
            result: DualValueNullableInfo[FieldType, Enum]|None = None

            for row in columns.AsIterable():
                result = getFieldType(str(row[1]))

                attributes = _Table.FieldAttributes.Null

                if result.GetKey() == FieldType.Integer: attributes |= _Table.FieldAttributes.Integer
                
                if checkAttributeValue(row, 2): attributes |= _Table.FieldAttributes.PrimaryKey
                if checkAttributeValue(row, 3): attributes |= _Table.FieldAttributes.NoDefault
                if checkAttributeValue(row, 4): attributes |= _Table.FieldAttributes.Nullable
                if checkAttributeValue(row, 5): attributes |= _Table.FieldAttributes.Unique

                yield GetField(fieldFactory, str(row[0]), getAttributes(attributes), result.GetKey(), result.GetValue())
        
        if self.__fields is None: self.__fields = self.__GetArray(getFields)
        
        return self.__fields

    @final
    def GetIndices(self) -> IArray[IIndex]:
        def getIndices() -> Iterable[IIndex]:
            def getIndices() -> Generator[IIndex]:
                func: Callable[[IIndexFactory, str, str, IndexKind, str, IList[str]], Generator[IIndex]|None]|None = None

                def checkIndexKind(factory: IIndexFactory, name: str, kind: IndexKind, columnName: str) -> IIndex|None: return factory.GetNormalIndex(name, columnName) if kind == IndexKind.Normal else None
                
                def getParser() -> Callable[[IIndexFactory, str, str, IndexKind, str, IList[str]], Generator[IIndex]|None]: return lambda factory, currentName, name, kind, columnName, columns: parse(factory, name, kind, columnName, columns)
                
                def getIndex(factory: IIndexFactory, currentName: str, kind: IndexKind, columns: IList[str]) -> IIndex:
                    def select() -> Iterable[str]: return columns.AsGenerator()

                    match kind:
                        case IndexKind.Unique: return factory.GetUnicityIndex(currentName, select())
                        case IndexKind.PrimaryKey: return factory.GetPrimaryKey(currentName, select())
                        
                        case _: raise ValueError("The index kind is not valid.")
                
                def _parse(factory: IIndexFactory, currentName: str, name: str, kind: IndexKind, columnName: str, columns: IList[str]) -> Generator[IIndex]|None:
                    nonlocal func

                    def push() -> None: columns.Push(columnName)
                    
                    def _getIndex() -> IIndex: return getIndex(factory, currentName, kind, columns)
                    
                    def getGenerator() -> Generator[IIndex]:
                        index: IIndex|None = checkIndexKind(factory, name, kind, columnName)

                        if index is None:
                            index = _getIndex()
                            
                            push()

                            yield index
                        
                        else:
                            yield _getIndex()

                            yield index
                    
                    if currentName == name:
                        push()

                        return None

                    func = getParser()

                    return getGenerator()
                
                def parse(factory: IIndexFactory, name: str, kind: IndexKind, columnName: str, columns: IList[str]) -> Generator[IIndex]|None:
                    # TODO: Use GROUP_CONCAT instead.

                    nonlocal func

                    def getGenerator(index: IIndex) -> Generator[IIndex]: yield index

                    index: IIndex|None = checkIndexKind(factory, name, kind, columnName)

                    if index is None:
                        columns.Push(columnName)

                        func = _parse

                        return None

                    return getGenerator(index)
                
                def executeQuery() -> ISelectionQueryExecutionResult|None:
                    query: ISelectionQuery = self.__GetQueryFactory().GetSelectionQuery(
                        TableParameterSet({
                            "PRAGMA_INDEX_LIST": TableParameter(
                                "il", MakeTableValueIterable(self.GetName()))}),
                        MakeColumnParameterSet(
                            TableColumn("il", "name"),
                            TableColumn("ii", "seqno"),
                            TableColumn("ii", "name"),
                            TableColumn("ii", "desc"),
                            TableColumn("ii", "coll"),
                            TableColumn("il", "partial")),
                        MakeConjunctionSet(
                            CreateDualResult(TableColumn("il", "name"), GetNotNullFieldParameter())))
                    
                    query.GetCases().Add(
                        ConditionSet[IndexKind, str](
                            "index_type",
                            IndexKind.Normal,
                            TableColumn("il", "origin"),
                            Dictionary[IndexKind, IParameter[IOperand[str]]]({
                                IndexKind.PrimaryKey: CreateFieldParameterFromValue(Operator.Equals, "pk"),
                                IndexKind.Unique: CreateFieldParameterFromValue(Operator.Equals, "u")}))) # TODO: or il."unique" = 1
                    
                    query.GetJoins().Add(
                        Join(
                            JoinType.Inner,
                            "PRAGMA_INDEX_XINFO",
                            TableParameter[IColumn](
                                "ii",
                                MakeTableColumnIterable(
                                    TableColumn("il", "name"))),
                            MakeConjunctionSet(
                                CreateDualResult(TableColumn("ii", "key"), CreateFieldParameterFromValue(Operator.Equals, 1)))))

                    # TODO: ORDER BY il.name, ii.seqno
                    
                    return query.Execute()

                indices: ISelectionQueryExecutionResult|None = executeQuery()

                if indices is None: return
                
                factory: IIndexFactory = self.__factoryProvider.GetIndexFactory()
                oldIndexName: str = ''
                newIndexName: str = ''
                indexKind: IndexKind = IndexKind.Null
                result: Generator[IIndex]|None = None
                columns: IList[str] = Queue[str]()
                func = getParser()

                for row in indices.AsIterable():
                    if (result := func(factory, oldIndexName, newIndexName := str(row[0]), indexKind := IndexKind(row[6]), str(row[2]), columns)) is None: oldIndexName = newIndexName

                    else:
                        for index in result: yield index
                
                if columns.HasItems(): yield getIndex(factory, newIndexName, indexKind, columns)
            
            def getForeignKeys() -> Generator[IIndex]:
                def executeQuery() -> ISelectionQueryExecutionResult|None:
                    def getColumn(name: str) -> TableColumn: return TableColumn("fk", name)
                    
                    query: ISelectionQuery = self.__GetQueryFactory().GetSelectionQuery(
                        TableParameterSet({
                            "PRAGMA_FOREIGN_KEY_LIST": TableParameter(
                                "fk", MakeTableValueIterable(self.GetName()))}),
                        MakeColumnParameterSet(
                            getColumn("id"),
                            getColumn("seq"),
                            getColumn("from"),
                            getColumn("table"),
                            getColumn("to"),
                            getColumn("on_update"),
                            getColumn("on_delete"),
                            getColumn("match")))

                        # TODO: ORDER BY fk.id, fk.seq
                    
                    return query.Execute()

                foreignKeys: ISelectionQueryExecutionResult|None = executeQuery()

                if foreignKeys is None: return
                
                factory: IIndexFactory = self.__factoryProvider.GetIndexFactory()

                for row in foreignKeys.AsIterable(): yield factory.GetForeignKey(str(row[0]), str(row[2]), CreateDualResult(str(row[3]), str(row[4])))

            return Append(getIndices(), getForeignKeys())

        if self.__indices is None: self.__indices = self.__GetArray(getIndices)
        
        return self.__indices
    
    def _Remove(self) -> None: self.__connection.Execute(f"DROP TABLE {self.GetName()}")
    
    def Dispose(self) -> None:
        self.__fields = None
        self.__connection.Dispose()

@final
class _DataBase(DataBaseAbstract):
    def __init__(self, connection: IFunction[_Connection]) -> None:
        super().__init__()

        self.__connection: IFunction[_Connection] = connection
    
    @staticmethod
    def __EnsureFields(fields: Iterable[IField]) -> None:
        EnsureOnlyOne(fields, lambda field: field.GetAttributes() == FieldAttributes.AutoIncrement, f"The '{FieldAttributes.AutoIncrement.name}' must be set to at most one field.")
    
    def __GetCursor(self) -> _Connection:
        return self.__connection()
    
    def _GetConnection(self) -> IConnection:
        return self.__GetCursor().GetConnection()
    
    def GetTableNames(self) -> Generator[str]:
        queryExecutionResult: ISelectionQueryExecutionResult|None = self._GetConnection().GetFactoryProvider().GetQueryFactory().GetSelectionQuery(
            TableParameterSet.CreateFromNames(
                "sqlite_master"),
            MakeColumnParameterSet(
                Column("name")),
            MakeConjunctionSet(
                CreateDualResult(Column("type"), CreateFieldParameterFromValue(Operator.Equals, "table")))).Execute()

        if queryExecutionResult is None: return

        for row in queryExecutionResult.AsIterable(): yield str(row[0])
    
    def _TryCreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> INullable[ITable]|None:
        _DataBase.__EnsureFields(fields)

        self.__TryCreateTable(name, fields, indices)

        return None
    def _CreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable:
        _DataBase.__EnsureFields(fields)
        
        return self.__CreateTable(name, fields, indices)
    
    def __GetTable(self, connection: _Connection, name: str) -> _Table:
        return _Table(connection, name)
    
    def __DoCreateTable(self, connection: sqlite3.Connection, query: str, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> None:
        connection.execute(f"CREATE TABLE {query}{self._GetConnection().FormatTableName(name)} ({", ".join(Select(Append(fields, indices), lambda item: item.ToString()))}) STRICT") # Fields must be quoted internally.
    def __TryCreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> None:
        self.__DoCreateTable(self.__GetCursor().GetInnerConnection(), "IF NOT EXISTS ", name, fields, indices)

        return None
    def __CreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable:
        connection: _Connection = self.__GetCursor()

        self.__DoCreateTable(connection.GetInnerConnection(), '', name, fields, indices)

        return self.__GetTable(connection, name)

    def _GetTable(self, name: str) -> ITable:
        return self.__GetTable(self.__GetCursor(), name)

@final
class _Struct(Disposable):
    @final
    class _Function(Abstract, IFunction[_Connection]):
        def __init__(self, struct: _Struct) -> None:
            super().__init__()

            self.__struct: _Struct = struct
        
        def GetValue(self) -> _Connection: return self.__struct._GetConnection()
    
    def __init__(self) -> None:
        super().__init__()

        self.__struct: IStruct[_Connection|None] = Struct[_Connection|None](None)
        self.__func: IFunction[_Connection] = _Struct._Function(self)
    
    def __GetValue(self) -> _Connection|None:
        return self.__struct.GetValue()
    
    def _GetConnection(self) -> _Connection:
        connection: _Connection|None = self.__GetValue()

        if connection is None: raise GetDiscardedError()
        
        return connection
    def GetConnection(self) -> IFunction[_Connection]:
        return self.__func
    
    def SetConnection(self, connection: _Connection) -> None:
        self.__struct.SetValue(connection)
    
    def _DisposeOverride(self, reason: DiscardReason) -> None:
        super()._DisposeOverride(reason)

        self.__struct.SetValue(None)
@final
class _QueryLimits(Abstract, IQueryLimits):
    def __init__(self, connection: Function[sqlite3.Connection]) -> None:
        super().__init__()

        self.__connection: Function[sqlite3.Connection] = connection
    
    def __GetLimit(self, value: int) -> int:
        return self.__connection().getlimit(value)

    def GetMaxParameterCount(self) -> DualValueBool[int]|None: return CreateDualValueBool(self.__GetLimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER), True)
    def GetMaxQuerySize(self) -> int|None: return self.__GetLimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH)

@final
class _FactoryProvider(Abstract, IFactoryProvider):
    def __init__(self, connection: IFunction[_Connection]) -> None:
        super().__init__()

        self.__connection: IFunction[_Connection] = connection
    
    def __GetConnection(self) -> IConnection:
        return self.__connection().GetConnection()
    
    def GetFieldFactory(self) -> IFieldFactory: return FieldFactory(self.__GetConnection())
    def GetQueryFactory(self) -> IQueryFactory: return Factory(self.__connection().GetInnerConnection())
    def GetIndexFactory(self) -> IIndexFactory: return IndexFactory(self.__GetConnection())

@final
class _TransactionCookie(TransactionCookie):
    @final
    class _TransactionControl(TransactionControl):
        def __init__(self, connection: sqlite3.Connection, cookie: ITransactionCookie) -> None:
            super().__init__(cookie)

            self.__connection: sqlite3.Connection = connection
        
        def __Execute(self, action: str) -> None:
            self.__connection.execute(action)

        def _BeginOverride(self) -> None: self.__Execute("BEGIN")
        
        def _CommitOverride(self) -> None: self.__Execute("COMMIT")
        def _RollbackOverride(self) -> None:
            if self.__connection.in_transaction: self.__Execute("ROLLBACK") # sqlite3_get_autocommit() instead of IsActive()
            
            # else: SQLite has already auto-reverted ; no exception
    
    def __init__(self, connection: Function[sqlite3.Connection]) -> None:
        super().__init__()

        self.__connection: Function[sqlite3.Connection]|None = connection
    
    def CreateTransactionControl(self) -> ITransactionControl:
        connection: Function[sqlite3.Connection]|None = self.__connection

        if connection is None: raise GetDiscardedError()

        return _TransactionCookie._TransactionControl(connection(), self)
    
    def Dispose(self) -> None:
        self.__connection = None

        super().Dispose()

@final
class Connection(ConnectionBase, IRevocableInfo):
    def __init__(self, path: str) -> None:
        super().__init__()

        self.__path: str = path
        self.__connection: _Struct = _Struct()
    
    def _CreateTransactionCookie(self) -> ITransactionCookie:
        return _TransactionCookie(self.__GetInnerConnection())
    
    def __GetConnection(self) -> IFunction[_Connection]: return self.__connection.GetConnection()
    def __GetInnerConnection(self) -> Function[sqlite3.Connection]: return lambda: self.__GetConnection()().GetInnerConnection()
    
    def _CreateCursor(self) -> IDataBase: return _DataBase(self.__GetConnection())
    
    def _CreateQueryLimits(self) -> IQueryLimits: return _QueryLimits(self.__GetInnerConnection())
    
    def _Open(self, queryLimits: IMutableQueryLimits) -> bool:
        self.__connection.SetConnection(_Connection(self, sqlite3.connect(self.__path, autocommit = True), queryLimits))

        return True
    
    def FormatTableName(self, name: str) -> str: return DoubleQuoteSurround(name)
    
    def _CreateFactoryProvider(self) -> IFactoryProvider: return _FactoryProvider(self.__GetConnection())
    
    def _CloseOverride(self) -> None: self.__connection.Dispose()
    
    def GetDiscardReason(self) -> DiscardReason: return self.__connection.GetDiscardReason()