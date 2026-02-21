from abc import abstractmethod
from typing import final

from WinCopies import IInterface

class __IGenericConstraint[TContainer, TInterface](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsContainer(self, container: TContainer) -> TInterface:
        pass
class __IGenericSpecializedConstraint[TContainer, TOverridden, TInterface, TSpecialized](__IGenericConstraint[TContainer, TInterface]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsSpecialized(self, container: TOverridden) -> TSpecialized:
        pass

class IGenericConstraint[TContainer, TInterface](__IGenericConstraint[TContainer, TInterface]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _TryAsContainer(self, container: TContainer|None) -> TInterface|None:
        return None if container is None else self._AsContainer(container)
class IGenericSpecializedConstraint[TContainer, TInterface, TSpecialized](IGenericConstraint[TContainer, TInterface], __IGenericSpecializedConstraint[TContainer, TContainer, TInterface, TSpecialized]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _TryAsSpecialized(self, container: TContainer|None) -> TSpecialized|None:
        return None if container is None else self._AsSpecialized(container)

class GenericConstraint[TContainer, TInterface](IGenericConstraint[TContainer, TInterface]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetContainer(self) -> TContainer:
        pass
    @final
    def _GetInnerContainer(self) -> TInterface:
        return self._AsContainer(self._GetContainer())
class GenericSpecializedConstraint[TContainer, TInterface, TSpecialized](GenericConstraint[TContainer, TInterface], IGenericSpecializedConstraint[TContainer, TInterface, TSpecialized]):
    def __init__(self) -> None:
        super().__init__()

    @final
    def _GetSpecializedContainer(self) -> TSpecialized:
        return self._AsSpecialized(self._GetContainer())

class IGenericConstraintImplementation[T](__IGenericConstraint[T, T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _AsContainer(self, container: T) -> T:
        return container
class IGenericSpecializedConstraintImplementation[TInterface, TSpecialized](IGenericConstraintImplementation[TInterface], __IGenericSpecializedConstraint[TInterface, TSpecialized, TInterface, TSpecialized]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _AsSpecialized(self, container: TSpecialized) -> TSpecialized:
        return container