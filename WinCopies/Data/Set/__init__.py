from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Typing import IString



from WinCopies.Data import IColumn, IOperandValue
from WinCopies.Data.Parameter import IParameter, ITableParameter

class IParameterSet[T](IDictionary[IColumn, T]):
    def __init__(self):
        super().__init__()

class IColumnParameterSet[T: IParameter[object]](IParameterSet[T|None]):
    def __init__(self):
        super().__init__()
class IFieldParameterSet[T: IParameter[IOperandValue]|None](IParameterSet[T]):
    def __init__(self):
        super().__init__()

class ITableParameterSet(IDictionary[IString, ITableParameter[object]|None]):
    def __init__(self):
        super().__init__()