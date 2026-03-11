from WinCopies.Collections.Expression import ICompositeExpressionRoot
from WinCopies.Collections.Extensions import IDictionary

from WinCopies.Typing.Object import IString
from WinCopies.Typing.Pairing import IKeyValuePair



from WinCopies.Data import ConditionalOperator, IColumn, IOperandValue
from WinCopies.Data.Parameter import IParameter, ITableParameter

class IParameterSet[T](IDictionary[IColumn, T]):
    def __init__(self) -> None:
        super().__init__()

class IColumnParameterSet[T: IParameter[object]](IParameterSet[T|None]):
    def __init__(self) -> None:
        super().__init__()
class IFieldParameterSet[TColumn: IColumn, TParameter: IParameter[IOperandValue]](ICompositeExpressionRoot[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator]):
    def __init__(self) -> None:
        super().__init__()

class IFieldConditionSet[T: IColumn](IFieldParameterSet[T, IParameter[IOperandValue]]):
    def __init__(self) -> None:
        super().__init__()

class ITableParameterSet(IDictionary[IString, ITableParameter[object]|None]):
    def __init__(self) -> None:
        super().__init__()