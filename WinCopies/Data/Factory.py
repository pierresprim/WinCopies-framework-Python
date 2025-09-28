from abc import abstractmethod
from collections.abc import Iterable

from WinCopies import IInterface
from WinCopies.Collections.Enumeration import ICountableEnumerable
from WinCopies.Collections.Extensions import IDictionary

from WinCopies.Data.Field import FieldAttributes, GenericField, BooleanField, IntegerField, RealField, TextField, IntegerMode, RealMode, TextMode
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.Query import ISelectionQuery, IInsertionQuery, IMultiInsertionQuery, IUpdateQuery
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet

from WinCopies.Typing import IString

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