from collections.abc import Iterable
from importlib import import_module
from inspect import getfile
from inspect import FrameInfo, stack, getfile
from os import path, sep
from sys import modules
from types import ModuleType, FrameType
from typing import List, Type

from WinCopies.Assertion import TryEnsureTrue, EnsureTrue
from WinCopies.String import SplitFromLast
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Converter, Selector

def __IsDirectCall(index: int, selector: Selector[str]) -> bool|None:
    frames: List[FrameInfo] = stack()

    nextIndex: int = index + 1

    if len(frames) > nextIndex:
        def getName(index: int) -> str:
            return selector(path.abspath(frames[index][1]))
        
        return getName(index) == getName(nextIndex)
    
    else:
        return None
def __EnsureDirectCall(index: int, selector: Converter[int, bool|None]) -> None:
    if not TryEnsureTrue(selector(index) == True):
        raise ValueError(index)

def __IsDirectModuleCall(index: int) -> bool|None:
    return __IsDirectCall(index, path.basename)
def __IsDirectPackageCall(index: int) -> bool|None:
    return __IsDirectCall(index, path.dirname)

def IsDirectModuleCall() -> bool|None:
    return __IsDirectModuleCall(3)
def EnsureDirectModuleCall() -> None:
    __EnsureDirectCall(4, __IsDirectModuleCall)

def IsDirectPackageCall() -> bool|None:
    return __IsDirectPackageCall(3)
def EnsureDirectPackageCall() -> None:
    __EnsureDirectCall(4, __IsDirectPackageCall)

def GetModuleName(module: ModuleType) -> str:
    return module.__name__ if hasattr(module, '__name__') else str(module)

def IsSubmoduleFromNames(moduleName: str, packageName: str) -> bool:
    return moduleName.startswith(packageName + '.')

def IsSubmodule(module: ModuleType, package: ModuleType) -> bool:
    return IsSubmoduleFromNames(GetModuleName(module), GetModuleName(package))
def ContainsModule(module: ModuleType, package: ModuleType) -> bool:
    moduleName: str = GetModuleName(module)
    packageName: str = GetModuleName(package)

    return moduleName == packageName or IsSubmoduleFromNames(moduleName, packageName)

def IsModuleInPackage(module: ModuleType, package: ModuleType) -> bool:
    # Check if module file is under package directory
    return path.abspath(getfile(module)).startswith(path.abspath(path.dirname(getfile(package))) + sep)
def TryIsModuleInPackage(module: ModuleType, package: ModuleType) -> bool|None:
    try:
        IsModuleInPackage(module, package)
    except TypeError:
        # Built-in modules don't have file paths
        return None

def EnsureIsSubmodule(module: ModuleType, package: ModuleType) -> None:
    EnsureTrue(IsSubmodule(module, package))
def EnsureModuleIsInPackage(module: ModuleType, package: ModuleType) -> None:
    EnsureTrue(IsModuleInPackage(module, package))

def TryGetModuleNameFromFrame(frame: FrameType) -> INullable[str|None]:
    moduleName: object|None = frame.f_globals.get('__name__')
    
    return GetNullable(None) if moduleName is None else (GetNullable(moduleName) if isinstance(moduleName, str) else GetNullValue())

def TryGetModuleFromFrame(frame: FrameType) -> INullable[ModuleType|None]:
    moduleName: str|None = TryGetModuleNameFromFrame(frame).TryGetValue()

    if moduleName is None:
        return GetNullable(None)
    
    module: ModuleType|None = modules.get(moduleName)

    if module is not None:
        return GetNullable(module)
    
    return GetNullValue()
def TryFindModuleFromFrameInfo(frameInfo: FrameInfo) -> ModuleType|None:
    fileName: str = frameInfo.filename

    for _, module in modules.items():
        if hasattr(module, '__file__') and module.__file__ == fileName:
            return module
    
    return None

def TryGetPackageNameFromFrame(frame: FrameType) -> str|None:
    def getValue(attributeName: str) -> object|None:
        return frame.f_globals.get(f"__{attributeName}__")
    
    # Try to get __package__ directly
    module: object|None = getValue("package")

    if isinstance(module, str):
        return module
    
    # Fall back to module name parsing
    module = getValue("name")

    return SplitFromLast(module, '.')[0] if isinstance(module, str) else None

def TryIsModuleInPackageFromFrame(frame: FrameType, package: ModuleType|str) -> bool:
    def tryGetModule() -> ModuleType|None:
        # Get module from frame
        module: INullable[ModuleType|None] = TryGetModuleFromFrame(frame)

        return module.GetValue() if module.HasValue() else None
    
    module: ModuleType|None = tryGetModule()

    if module is None:
        return False
    
    if isinstance(package, str):
        package = import_module(package)
    
    try:
        return IsModuleInPackage(module, package)
    
    except (TypeError, ImportError):
        # Fallback to name checking
        def getName(module: ModuleType) -> str:
            return getattr(module, "__name__", '')
        
        return IsSubmoduleFromNames(getName(module), getName(package))

def IsSubclass[T](cls: Type[T], types: Iterable[Type[T]]) -> bool:
    for type in types:
        if issubclass(cls, type):
            return True
    
    return False
def IsSubclassOf[T](cls: Type[T], *types: Type[T]) -> bool:
    return IsSubclass(cls, types)

def Is[T](obj: T, types: Iterable[Type[T]]) -> bool:
    return IsSubclass(type(obj), types)
def IsOf[T](obj: T, *types: Type[T]) -> bool:
    return Is(obj, types)

def Implements[T](cls: Type[T], types: Iterable[Type[T]]) -> bool:
    for type in types:
        if not issubclass(cls, type):
            return False
    
    return True
def ImplementsAll[T](cls: Type[T], *types: Type[T]) -> bool:
    return Implements(cls, types)

def IsFrom[T](obj: T, types: Iterable[Type[T]]) -> bool:
    return Implements(type(obj), types)
def IsFromAll[T](obj: T, *types: Type[T]) -> bool:
    return IsFrom(obj, types)

def AreInstances(type: type, *values: object) -> bool:
    for value in values:
        if not isinstance(value, type):
            return False
    
    return True