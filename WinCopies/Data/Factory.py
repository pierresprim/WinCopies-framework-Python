from abc import abstractmethod
from collections.abc import Iterable

from WinCopies.Collections.Extensions import IDictionary

from WinCopies.Data.Field import FieldAttributes, GenericField, BooleanField, IntegerField, RealField, TextField, IntegerMode, RealMode, TextMode
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.Query import ISelectionQuery, IInsertionQuery, IMultiInsertionQuery
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet

class IFieldFactory:
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

class IQueryFactory:
    @abstractmethod
    def GetSelectionQuery(self, tables: ITableParameterSet, columns: IColumnParameterSet[IParameter[object]], conditions: IConditionParameterSet|None = None) -> ISelectionQuery:
        pass

    @abstractmethod
    def GetInsertionQuery(self, tableName: str, items: IDictionary[str, object]) -> IInsertionQuery:
        pass

    @abstractmethod
    def GetMultiInsertionQuery(self, tableName: str, items: Iterable[Iterable[object]], *columns: str) -> IMultiInsertionQuery:
        pass