from __future__ import annotations

from abc import abstractmethod
from typing import final



from WinCopies import IInterface
from WinCopies.Collections.Enumeration import IEnumerable
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyEnumerable
from WinCopies.Collections.Expression import ICompositeExpression
from WinCopies.Collections.Extensions import IDictionary

from WinCopies.Typing import INullable
from WinCopies.Typing.Pairing import IKeyValuePair, TryGetKey, TryGetValue



from WinCopies.Data import ConditionalOperator, IColumn, IOperandValue
from WinCopies.Data.Parameter import IFormattable, IParameter, ITableParameter

class IFieldParameterSetItem[TColumn: IColumn, TParameter: IParameter[IOperandValue]](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetFieldParameter(self) -> IKeyValuePair[TColumn, TParameter|None]|None:
        ...
    
    @final
    def TryGetColumn(self) -> INullable[TColumn]:
        return TryGetKey(self.TryGetFieldParameter())
    @final
    def TryGetParameter(self) -> INullable[TParameter|None]:
        return TryGetValue(self.TryGetFieldParameter())
    
    @abstractmethod
    def TryGetItems(self) -> IEnumerable[IFieldParameterSetItem[TColumn, TParameter]]|None:
        ...

    @abstractmethod
    def TryGetPreviousOperator(self) -> ConditionalOperator|None:
        ...
    @abstractmethod
    def TryGetNextOperator(self) -> ConditionalOperator|None:
        ...
class IFieldConditionSetItem[T: IColumn](IFieldParameterSetItem[T, IParameter[IOperandValue]]):
    def __init__(self) -> None: super().__init__()

class IFieldParameterRecursivelyEnumerable[TColumn: IColumn, TParameter: IParameter[IOperandValue]](IRecursivelyEnumerable[IFieldParameterSetItem[TColumn, TParameter]]):
    def __init__(self) -> None: super().__init__()
class IFieldConditionRecursivelyEnumerable[T: IColumn](IFieldParameterRecursivelyEnumerable[T, IParameter[IOperandValue]]):
    def __init__(self) -> None: super().__init__()

type IFieldConditionSetItemAlias[T: IColumn] = IFieldParameterSetItem[T, IParameter[IOperandValue]]

type IFieldParameterRecursivelyEnumerableAlias[TColumn: IColumn, TParameter: IParameter[IOperandValue]] = IRecursivelyEnumerable[IFieldParameterSetItem[TColumn, TParameter]]
type IFieldConditionRecursivelyEnumerableAlias[T: IColumn] = IFieldParameterRecursivelyEnumerableAlias[T, IParameter[IOperandValue]]

class IParameterSet[T](IDictionary[IColumn, T]):
    def __init__(self) -> None: super().__init__()

class IColumnParameterSet[T: IFormattable](IParameterSet[T|None]):
    def __init__(self) -> None: super().__init__()
class IFieldParameterSet[TColumn: IColumn, TParameter: IParameter[IOperandValue]](IRecursivelyEnumerable[ICompositeExpression[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator]]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsRecursivelyParameterEnumerable(self) -> IFieldParameterRecursivelyEnumerableAlias[TColumn, TParameter]:
        ...

class IFieldConditionSet[T: IColumn](IFieldParameterSet[T, IParameter[IOperandValue]]):
    def __init__(self) -> None: super().__init__()

class ITableParameterSet(IDictionary[str, ITableParameter[object]|None]):
    def __init__(self) -> None: super().__init__()