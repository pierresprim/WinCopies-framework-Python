from abc import abstractmethod
from collections.abc import Iterable

from WinCopies import IInterface
from WinCopies.Collections.Enumeration import ICountableEnumerable
from WinCopies.Collections.Extensions import IEquatableTuple, IDictionary

from WinCopies.Data.Field import FieldAttributes, GenericField, BooleanField, IntegerField, RealField, TextField, IntegerMode, RealMode, TextMode
from WinCopies.Data.Index import ISingleColumnIndex, IMultiColumnIndex, IMultiColumnKey, IForeignKey
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.Query import ISelectionQuery, IInsertionQuery, IMultiInsertionQuery, IUpdateQuery
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet

from WinCopies.Typing.Object import IString
from WinCopies.Typing.Pairing import DualResult

class IFieldFactory(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def CreateNull(self, name: str, attribute: FieldAttributes) -> GenericField:
        pass

    @abstractmethod
    def CreateBool(self, name: str, attribute: FieldAttributes) -> BooleanField:
        pass
    
    @abstractmethod
    def CreateInteger(self, name: str, attribute: FieldAttributes, mode: IntegerMode) -> IntegerField:
        pass
    @abstractmethod
    def CreateReal(self, name: str, attribute: FieldAttributes, mode: RealMode) -> RealField:
        pass
    @abstractmethod
    def CreateText(self, name: str, attribute: FieldAttributes, mode: TextMode) -> TextField:
        pass

class IQueryFactory(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetSelectionQuery(self, tables: ITableParameterSet, columns: IColumnParameterSet[IParameter[object]], conditions: IConditionParameterSet|None = None) -> ISelectionQuery:
        pass

    @abstractmethod
    def GetInsertionQuery(self, tableName: str, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
        pass
    @abstractmethod
    def GetMultiInsertionQuery(self, tableName: str, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
        pass
    
    @abstractmethod
    def GetUpdateQuery(self, tableName: str, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> IUpdateQuery:
        pass

class ITableQueryFactory(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetSelectionQuery(self, columns: IColumnParameterSet[IParameter[object]], conditions: IConditionParameterSet|None = None) -> ISelectionQuery:
        pass

    @abstractmethod
    def GetInsertionQuery(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
        pass
    @abstractmethod
    def GetMultiInsertionQuery(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
        pass
    
    @abstractmethod
    def GetUpdateQuery(self, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> IUpdateQuery:
        pass

class IIndexFactory(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetPrimaryKey(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString]) -> IMultiColumnKey:
        pass
    @abstractmethod
    def GetForeignKey(self, name: str, column: str, foreignKey: DualResult[str, str]) -> IForeignKey:
        pass
    @abstractmethod
    def GetNormalIndex(self, name: str, column: str) -> ISingleColumnIndex:
        pass
    @abstractmethod
    def GetUnicityIndex(self, name: str, columns: IEquatableTuple[IString]|Iterable[IString]) -> IMultiColumnIndex:
        pass