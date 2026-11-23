from abc import abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import final



import WinCopies.Data

from WinCopies import Abstract, String
from WinCopies.Collections.Extensions import IHashableTuple
from WinCopies.Collections.Iteration import Select
from WinCopies.Enum import HasFlag
from WinCopies.String import CommaJoin
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Pairing import DualResult
from WinCopies.Typing.Reflection import EnsureDirectPackageCall, EnsureCallerPackage



from WinCopies.Data import Field
from WinCopies.Data.Abstract import IConnection
from WinCopies.Data.Factory import IFieldFactory, IIndexFactory
from WinCopies.Data.Field import FieldAttributes, IntegerMode, RealMode, TextMode, IField
from WinCopies.Data.Index import IndexType, IIndex, IKey, ISingleColumnIndex, IMultiColumnIndex, IMultiColumnKey, IForeignKey, UnicityIndex, PrimaryKey, ForeignKey

@final
class FieldFactory(Abstract, IFieldFactory):
    class _FieldBase(Abstract, IField):
        def __init__(self) -> None:
            EnsureCallerPackage(WinCopies.Data)
            
            super().__init__()
        
        @abstractmethod
        def _GetConnection(self) -> IConnection:
            ...
        
        def ToString(self) -> str:
            def getEnumName(enum: Enum) -> str: return enum.name.upper()
            
            def getAttributes(attributes: FieldAttributes) -> str|None:
                def notNullJoin(*values: str) -> str: return String.SpaceJoinValues(*values, "NOT NULL")
                def getAutoIncrement() -> str: return notNullJoin(getEnumName(FieldAttributes.AutoIncrement), getEnumName(FieldAttributes.Unique))
                
                def check(value: FieldAttributes) -> bool: return HasFlag(attributes, value)
                
                if attributes == FieldAttributes.Null: return "NOT NULL"
                
                if check(FieldAttributes.PrimaryKey): return String.SurroundWithSpace("PRIMARY KEY", getAutoIncrement())
                if check(FieldAttributes.AutoIncrement): return getAutoIncrement()
                if check(FieldAttributes.Unique): return notNullJoin(getEnumName(FieldAttributes.Unique))
                if check(FieldAttributes.Nullable): return None
                
                raise ValueError()
            
            def getField() -> str: return f"{self._GetConnection().FormatTableName(self.GetName())} {getEnumName(self.GetType())}"
                
            result: str|None = getAttributes(self.GetAttributes())
            
            return getField() if result is None else f"{getField()} {result}"
    
    @final
    class __GenericField(Field.GenericField, _FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes, connection: IConnection) -> None:
            super().__init__(name, attribute)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
    
    @final
    class __BooleanField(Field.BooleanField, _FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes, connection: IConnection) -> None:
            super().__init__(name, attribute)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
    
    @final
    class __IntegerField(Field.IntegerField, _FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes, mode: IntegerMode, connection: IConnection) -> None:
            super().__init__(name, attribute, mode)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
    @final
    class __RealField(Field.RealField, _FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes, mode: RealMode, connection: IConnection) -> None:
            super().__init__(name, attribute, mode)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
    @final
    class __TextField(Field.TextField, _FieldBase):
        def __init__(self, name: str, attribute: FieldAttributes, mode: TextMode, connection: IConnection) -> None:
            super().__init__(name, attribute, mode)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
    
    def __init__(self, connection: IConnection) -> None:
        EnsureDirectPackageCall()
        
        super().__init__()

        self.__connection: IConnection = connection
    
    def CreateNull(self, name: str, attribute: FieldAttributes) -> Field.GenericField: return FieldFactory.__GenericField(name, attribute, self.__connection)
    
    def CreateBool(self, name: str, attribute: FieldAttributes) -> Field.BooleanField: return FieldFactory.__BooleanField(name, attribute, self.__connection)
    
    def CreateInteger(self, name: str, attribute: FieldAttributes, mode: IntegerMode) -> Field.IntegerField: return FieldFactory.__IntegerField(name, attribute, mode, self.__connection)
    def CreateReal(self, name: str, attribute: FieldAttributes, mode: RealMode) -> Field.RealField: return FieldFactory.__RealField(name, attribute, mode, self.__connection)
    def CreateText(self, name: str, attribute: FieldAttributes, mode: TextMode) -> Field.TextField: return FieldFactory.__TextField(name, attribute, mode, self.__connection)

@final
class IndexFactory(Abstract, IIndexFactory):
    class _Index(Abstract, IIndex):
        def __init__(self) -> None:
            EnsureCallerPackage(WinCopies.Data)
            
            super().__init__()

        @abstractmethod
        def _GetConnection(self) -> IConnection:
            ...
        
        @abstractmethod
        def _GetStringType(self) -> str:
            ...

        @final
        def _FormatTableName(self, name: str) -> str:
            return self._GetConnection().FormatTableName(name)
        
        @final
        def _GetHeader(self) -> str:
            return f"CONSTRAINT {self._FormatTableName(self.GetName())} {self._GetStringType()}"
    class _MultiColumnIndex(_Index, IMultiColumnIndex):
        def __init__(self) -> None: super().__init__()
        
        @final
        def _GetStringColumns(self) -> str:
            return f"({CommaJoin(Select(self.GetColumns().AsIterable(), lambda columnName: self._FormatTableName(columnName)))})"
        
        def ToString(self) -> str:
            return f"{self._GetHeader()} {self._GetStringColumns()}"
    @final
    class __UnicityIndex(UnicityIndex, _MultiColumnIndex):
        def __init__(self, name: str, columns: IHashableTuple[str]|Iterable[str], connection: IConnection) -> None:
            super().__init__(name, columns)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
        
        def _GetStringType(self) -> str:
            return IndexType.Unique.name.upper()
    class _Key(_Index, IKey):
        def __init__(self) -> None: super().__init__()
        
        def _GetStringType(self) -> str:
            return f"{self.GetKeyType().name.upper()} {IndexType.Key.name.upper()}"
    @final
    class __PrimaryKey(PrimaryKey, _MultiColumnIndex, _Key):
        def __init__(self, name: str, columns: IHashableTuple[str]|Iterable[str], connection: IConnection) -> None:
            super().__init__(name, columns)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
    @final
    class __ForeignKey(ForeignKey, _Key):
        def __init__(self, name: str, column: str, foreignKey: DualResult[str, str], connection: IConnection) -> None:
            super().__init__(name, column, foreignKey)

            self.__connection: IConnection = connection
        
        def _GetConnection(self) -> IConnection:
            return self.__connection
        
        def ToString(self) -> str:
            foreignKey: DualResult[str, str] = self.GetForeignKey()

            return f"{self._GetHeader()} REFERENCES {self._FormatTableName(foreignKey.GetKey())} ({self._FormatTableName(foreignKey.GetValue())})"
    
    def __init__(self, connection: IConnection) -> None:
        EnsureDirectPackageCall()
        
        super().__init__()

        self.__connection: IConnection = connection
    
    def _GetConnection(self) -> IConnection:
        return self.__connection
    
    @final
    def GetPrimaryKey(self, name: str, columns: IHashableTuple[str]|Iterable[str]) -> IMultiColumnKey: return IndexFactory.__PrimaryKey(name, columns, self._GetConnection())
    @final
    def GetForeignKey(self, name: str, column: str, foreignKey: DualResult[str, str]) -> IForeignKey: return IndexFactory.__ForeignKey(name, column, foreignKey, self._GetConnection())
    @final
    def GetNormalIndex(self, name: str, column: str) -> ISingleColumnIndex: raise InvalidOperationError("Not supported.")
    @final
    def GetUnicityIndex(self, name: str, columns: IHashableTuple[str]|Iterable[str]) -> IMultiColumnIndex: return IndexFactory.__UnicityIndex(name, columns, self._GetConnection())