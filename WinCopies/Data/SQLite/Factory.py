from abc import abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import final

import sqlite3



import WinCopies.Data

from WinCopies import String
from WinCopies.Collections.Enumeration import ICountableEnumerable
from WinCopies.Collections.Extensions import IEquatableTuple, IDictionary
from WinCopies.Collections.Iteration import Select
from WinCopies.Enum import HasFlag
from WinCopies.String import CommaJoin
from WinCopies.Typing import InvalidOperationError, IString
from WinCopies.Typing.Pairing import DualResult
from WinCopies.Typing.Reflection import EnsureDirectPackageCall, EnsureCallerPackage



from WinCopies.Data import Field
from WinCopies.Data.Abstract import IConnection
from WinCopies.Data.Factory import IFieldFactory, IQueryFactory, IIndexFactory
from WinCopies.Data.Field import FieldAttributes, IntegerMode, RealMode, TextMode, IField
from WinCopies.Data.Index import IndexType, IIndex, IKey, ISingleColumnIndex, IMultiColumnIndex, IMultiColumnKey, IForeignKey, UnicityIndex, PrimaryKey, ForeignKey
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.Query import ISelectionQuery, IInsertionQuery, IMultiInsertionQuery, IUpdateQuery
from WinCopies.Data.Set import ITableParameterSet, IColumnParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet

from WinCopies.Data.SQLite.Query import SelectionQuery, InsertionQuery, MultiInsertionQuery, UpdateQuery

@final
class FieldFactory(IFieldFactory):
    class FieldBase(IField):
        def __init__(self):
            EnsureCallerPackage(WinCopies.Data)
            
            super().__init__()
        
        def ToString(self) -> str:
            def getEnumName(enum: Enum) -> str:
                return enum.name.upper()
            
            def getAttributes(attributes: FieldAttributes) -> str|None:
                def notNullJoin(*values: str) -> str:
                    return String.SpaceJoinValues(*values, "NOT NULL")
                def getAutoIncrement() -> str:
                    return notNullJoin(getEnumName(FieldAttributes.AutoIncrement), getEnumName(FieldAttributes.Unique))
                
                def check(value: FieldAttributes) -> bool:
                    return HasFlag(attributes, value)
                
                if attributes == FieldAttributes.Null:
                    return "NOT NULL"
                
                if check(FieldAttributes.PrimaryKey):
                    return String.SurroundWithSpace("PRIMARY KEY", getAutoIncrement())
                
                if check(FieldAttributes.AutoIncrement):
                    return getAutoIncrement()
                
                if check(FieldAttributes.Unique):
                    return notNullJoin(getEnumName(FieldAttributes.Unique))
                
                if check(FieldAttributes.Nullable):
                    return None
                
                raise ValueError()
            
            def getField() -> str:
                return f"{self.GetName()} {getEnumName(self.GetType())}"
                
            result: str|None = getAttributes(self.GetAttributes())
            
            return getField() if result is None else f"{getField()} {result}"
    
    @final
    class __GenericField(Field.GenericField, FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes):
            super().__init__(name, attribute)
    
    @final
    class __BooleanField(Field.BooleanField, FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes):
            super().__init__(name, attribute)
    
    @final
    class __IntergerField(Field.IntegerField, FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes, mode: IntegerMode):
            super().__init__(name, attribute, mode)
    @final
    class __RealField(Field.RealField, FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes, mode: RealMode):
            super().__init__(name, attribute, mode)
    @final
    class __TextField(Field.TextField, FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes, mode: TextMode):
            super().__init__(name, attribute, mode)
    
    def __init__(self):
        EnsureDirectPackageCall()
        
        super().__init__()
    
    def CreateNull(self, name: str, attribute: FieldAttributes) -> Field.GenericField:
        return FieldFactory.__GenericField(name, attribute)
    
    def CreateBool(self, name: str, attribute: FieldAttributes) -> Field.BooleanField:
        return FieldFactory.__BooleanField(name, attribute)
    
    def CreateInteger(self, name: str, attribute: FieldAttributes, mode: IntegerMode) -> __IntergerField:
        return FieldFactory.__IntergerField(name, attribute, mode)
    def CreateReal(self, name: str, attribute: FieldAttributes, mode: RealMode) -> __RealField:
        return FieldFactory.__RealField(name, attribute, mode)
    def CreateText(self, name: str, attribute: FieldAttributes, mode: TextMode) -> __TextField:
        return FieldFactory.__TextField(name, attribute, mode)

@final
class QueryFactory(IQueryFactory):
    def __init__(self, connection: sqlite3.Connection):
        EnsureDirectPackageCall()

        super().__init__()

        self.__connection: sqlite3.Connection = connection
    
    def _GetConnection(self) -> sqlite3.Connection:
        return self.__connection
    
    def GetSelectionQuery(self, tables: ITableParameterSet, columns: IColumnParameterSet[IParameter[object]], conditions: IConditionParameterSet|None = None) -> ISelectionQuery:
        return SelectionQuery(self._GetConnection(), tables, columns, conditions)
    
    def GetInsertionQuery(self, tableName: str, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
        return InsertionQuery(self._GetConnection(), tableName, items, ignoreExisting)
    def GetMultiInsertionQuery(self, tableName: str, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
        return MultiInsertionQuery(self._GetConnection(), tableName, columns, items, ignoreExisting)
    
    def GetUpdateQuery(self, tableName: str, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> IUpdateQuery:
        return UpdateQuery(self._GetConnection(), tableName, values, conditions)

@final
class IndexFactory(IIndexFactory):
    class _Index(IIndex):
        def __init__(self):
            EnsureCallerPackage(WinCopies.Data)

            super().__init__()

        @abstractmethod
        def _GetConnection(self) -> IConnection:
            pass
        
        @abstractmethod
        def _GetStringType(self) -> str:
            pass

        @final
        def _FormatTableName(self, name: str) -> str:
            return self._GetConnection().FormatTableName(name)
        
        @final
        def _GetHeader(self) -> str:
            return f"CONSTRAINT {self._FormatTableName(self.GetName())} {self._GetStringType()}"
    class _MultiColumnIndex(_Index, IMultiColumnIndex):
        def __init__(self):
            super().__init__()
        
        @final
        def _GetStringColumns(self) -> str:
            return f"({CommaJoin(Select(self.GetColumns().AsIterable(), lambda columnName: self._FormatTableName(columnName.ToString())))})"
        
        def ToString(self) -> str:
            return f"{self._GetHeader()} {self._GetStringColumns()}"
    @final
    class __UnicityIndex(UnicityIndex, _MultiColumnIndex):
        def __init__(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString], connection: IConnection):
            super().__init__(name, columns)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
        
        def _GetStringType(self) -> str:
            return IndexType.Unique.name.upper()
    class _Key(_Index, IKey):
        def __init__(self):
            super().__init__()
        
        def _GetStringType(self) -> str:
            return f"{self.GetKeyType().name.upper()} {IndexType.Key.name.upper()}"
    @final
    class __PrimaryKey(PrimaryKey, _MultiColumnIndex, _Key):
        def __init__(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString], connection: IConnection):
            super().__init__(name, columns)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
    @final
    class __ForeignKey(ForeignKey, _Key):
        def __init__(self, name: str, column: str, foreignKey: DualResult[str, str], connection: IConnection):
            super().__init__(name, column, foreignKey)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
        
        def ToString(self) -> str:
            foreignKey: DualResult[str, str] = self.GetForeignKey()

            return f"{super().ToString()} REFERENCES {self._FormatTableName(foreignKey.GetKey())} ({self._FormatTableName(foreignKey.GetValue())})"
    
    def __init__(self, connection: IConnection):
        EnsureDirectPackageCall()
        
        super().__init__()

        self.__connection: IConnection = connection
    
    def _GetConnection(self) -> IConnection:
        return self.__connection
    
    @final
    def GetPrimaryKey(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString]) -> IMultiColumnKey:
        return IndexFactory.__PrimaryKey(name, columns, self._GetConnection())
    @final
    def GetForeignKey(self, name: str, column: str, foreignKey: DualResult[str, str]) -> IForeignKey:
        return IndexFactory.__ForeignKey(name, column, foreignKey, self._GetConnection())
    @final
    def GetNormalIndex(self, name: str, column: str) -> ISingleColumnIndex:
        raise InvalidOperationError("Not supported.")
    @final
    def GetUnicityIndex(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString]) -> IMultiColumnIndex:
        return IndexFactory.__UnicityIndex(name, columns, self._GetConnection())