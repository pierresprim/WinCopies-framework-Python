from collections.abc import Iterable
from importlib import import_module
from inspect import getfile
from inspect import FrameInfo, stack, getfile
from os import path, sep
from sys import modules, builtin_module_names
from types import ModuleType, FrameType
from typing import List, Type

from WinCopies.Assertion import TryEnsureTrue, EnsureTrue
from WinCopies.Collections import Generator
from WinCopies.String import SplitFromLast
from WinCopies.Typing import InvalidOperationError, INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Converter, Selector

def __IsDirectCall(index: int, selector: Selector[str]) -> bool|None:
    frames: List[FrameInfo] = stack()
    
    nextIndex: int = index + 1

    if len(frames) > nextIndex:
        def getName(index: int) -> str:
            return selector(path.abspath(frames[index].filename))
        
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
    """Checks if the caller is directly calling from the same module.

    Returns:
        True if direct module call, False if not, None if insufficient stack frames.
    """
    return __IsDirectModuleCall(3)
def EnsureDirectModuleCall() -> None:
    """Ensures the caller is directly calling from the same module.

    Raises:
        AssertionError: If the call is not direct or if insufficient stack frames.
    """
    __EnsureDirectCall(4, __IsDirectModuleCall)

def IsDirectPackageCall() -> bool|None:
    """Checks if the caller is directly calling from the same package.

    Returns:
        True if direct package call, False if not, None if insufficient stack frames.
    """
    return __IsDirectPackageCall(3)
def EnsureDirectPackageCall() -> None:
    """Ensures the caller is directly calling from the same package.

    Raises:
        AssertionError: If the call is not direct or if insufficient stack frames.
    """
    __EnsureDirectCall(4, __IsDirectPackageCall)

def GetModuleName(module: ModuleType) -> str:
    """Gets the name of a module.

    Args:
        module: The module to get the name from.

    Returns:
        The module's __name__ attribute if available, otherwise its string representation.
    """
    return module.__name__ if hasattr(module, "__name__") else str(module)

def IsSubmoduleFromNames(moduleName: str, packageName: str) -> bool:
    """Checks if a module name represents a submodule of a package name.

    Args:
        moduleName: The name of the module to check.
        packageName: The name of the package.

    Returns:
        True if the module is a submodule of the package, False otherwise.
    """
    return moduleName.startswith(packageName + '.')

def IsSubmodule(module: ModuleType, package: ModuleType) -> bool:
    """Checks if a module is a submodule of a package.

    Args:
        module: The module to check.
        package: The package.

    Returns:
        True if the module is a submodule of the package, False otherwise.
    """
    return IsSubmoduleFromNames(GetModuleName(module), GetModuleName(package))
def ContainsModule(module: ModuleType, package: ModuleType) -> bool:
    """Checks if a package contains a module (either as itself or as a submodule).

    Args:
        module: The module to check.
        package: The package.

    Returns:
        True if the module is the package itself or a submodule of it, False otherwise.
    """
    moduleName: str = GetModuleName(module)
    packageName: str = GetModuleName(package)

    return moduleName == packageName or IsSubmoduleFromNames(moduleName, packageName)

def IsModuleInPackage(module: ModuleType, package: ModuleType) -> bool:
    """Checks if a module's file is located under a package's directory.

    Args:
        module: The module to check.
        package: The package.

    Returns:
        True if the module file is under the package directory, False otherwise.

    Raises:
        TypeError: If module or package is built-in and has no file path.
    """
    return path.abspath(getfile(module)).startswith(path.abspath(path.dirname(getfile(package))) + sep)
def TryIsModuleInPackage(module: ModuleType, package: ModuleType) -> bool|None:
    """Tries to check if a module's file is located under a package's directory.

    Args:
        module: The module to check.
        package: The package.

    Returns:
        True if the module file is under the package directory, False otherwise, None if built-in module.
    """
    try:
        IsModuleInPackage(module, package)
    except TypeError:
        return None

def EnsureIsSubmodule(module: ModuleType, package: ModuleType) -> None:
    """Ensures a module is a submodule of a package.

    Args:
        module: The module to check.
        package: The package.

    Raises:
        AssertionError: If the module is not a submodule of the package.
    """
    EnsureTrue(IsSubmodule(module, package))
def EnsureModuleIsInPackage(module: ModuleType, package: ModuleType) -> None:
    """Ensures a module's file is located under a package's directory.

    Args:
        module: The module to check.
        package: The package.

    Raises:
        AssertionError: If the module file is not under the package directory.
        TypeError: If module or package is built-in and has no file path.
    """
    EnsureTrue(IsModuleInPackage(module, package))

def TryGetModuleNameFromFrame(frame: FrameType) -> INullable[str|None]:
    """Tries to get the module name from a frame.

    Args:
        frame: The frame to extract the module name from.

    Returns:
        INullable with None if not found, with the name if found, or null value if invalid type.
    """
    moduleName: object|None = frame.f_globals.get('__name__')

    return GetNullable(None) if moduleName is None else (GetNullable(moduleName) if isinstance(moduleName, str) else GetNullValue())

def TryGetModuleFromFrame(frame: FrameType) -> INullable[ModuleType|None]:
    """Tries to get the module from a frame.

    Args:
        frame: The frame to extract the module from.

    Returns:
        INullable with None if module name not found, with the module if found, or null value if module not in sys.modules.
    """
    moduleName: str|None = TryGetModuleNameFromFrame(frame).TryGetValue()

    if moduleName is None:
        return GetNullable(None)

    module: ModuleType|None = modules.get(moduleName)

    if module is not None:
        return GetNullable(module)

    return GetNullValue()

def TryFindModuleFromFileName(fileName: str) -> ModuleType|None:
    """Tries to find a module by its file name in sys.modules.

    Args:
        fileName: The file name to search for.

    Returns:
        The module if found, None otherwise.
    """
    for _, module in modules.items():
        if hasattr(module, '__file__') and module.__file__ == fileName:
            return module

    return None

def TryGetPackageNameFromFrame(frame: FrameType) -> str|None:
    """Tries to get the package name from a frame.

    Args:
        frame: The frame to extract the package name from.

    Returns:
        The package name if found, None otherwise.
    """
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
    """Tries to check if the module from a frame is in a package.

    Args:
        frame: The frame to extract the module from.
        package: The package (as ModuleType or string name).

    Returns:
        True if the module is in the package, False otherwise.
    """
    def tryGetModule() -> ModuleType|None:
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

def __TryOnModuleNameFromFrame[T](frame: FrameType, func: Converter[str, T]) -> INullable[T|None]:
    result: INullable[str|None] = TryGetModuleNameFromFrame(frame)

    if result.HasValue():
        value: str|None = result.GetValue()

        return GetNullable(None if value is None else func(value))
    
    return GetNullValue()
def IsMain(moduleName: str) -> bool:
    """Checks if a module name is '__main__'.

    Args:
        moduleName: The module name to check.

    Returns:
        True if the module name is '__main__', False otherwise.
    """
    return moduleName == '__main__'
def TryIsMain(frame: FrameType) -> INullable[bool|None]:
    """Tries to check if the module from a frame is '__main__'.

    Args:
        frame: The frame to check.

    Returns:
        INullable with None if module name not found, with bool result if found, or null value if invalid.
    """
    return __TryOnModuleNameFromFrame(frame, IsMain)

def IsBuiltin(moduleName: str) -> bool:
    """Checks if a module name is a built-in module.

    Args:
        moduleName: The module name to check.

    Returns:
        True if the module is built-in, False otherwise.
    """
    return moduleName in builtin_module_names
def TryIsBuiltin(frame: FrameType) -> INullable[bool|None]:
    """Tries to check if the module from a frame is built-in.

    Args:
        frame: The frame to check.

    Returns:
        INullable with None if module name not found, with bool result if found, or null value if invalid.
    """
    return __TryOnModuleNameFromFrame(frame, IsBuiltin)

def EnumerateFromCallStack() -> Generator[FrameInfo]:
    """Enumerates all frames from the call stack.

    Yields:
        FrameInfo objects from the call stack.
    """
    for frame in stack():
        yield frame

def __CheckCallerPackage(targetPackage: ModuleType|str, index: int) -> bool:
    return TryIsModuleInPackageFromFrame(stack()[index].frame, targetPackage)

def CheckCallerPackage(targetPackage: ModuleType|str) -> bool:
    """Checks if the caller is from a specific package.

    Args:
        targetPackage: The package to check (as ModuleType or string name).

    Returns:
        True if the caller is from the target package, False otherwise.
    """
    return __CheckCallerPackage(targetPackage, 1)
def EnsureCallerPackage(targetPackage: ModuleType|str) -> None:
    """Ensures the caller is from a specific package.

    Args:
        targetPackage: The package to check (as ModuleType or string name).

    Raises:
        InvalidOperationError: If the caller is not from the target package.
    """
    if not __CheckCallerPackage(targetPackage, 2):
        raise InvalidOperationError(f"This function can only be called from {targetPackage}.")

def IsSubclass[T](cls: Type[T], types: Iterable[Type[T]]) -> bool:
    """Checks if a class is a subclass of any type in an iterable.

    Args:
        cls: The class to check.
        types: The types to check against.

    Returns:
        True if the class is a subclass of at least one type, False otherwise.
    """
    for type in types:
        if issubclass(cls, type):
            return True

    return False
def IsSubclassOf[T](cls: Type[T], *types: Type[T]) -> bool:
    """Checks if a class is a subclass of any type in variadic arguments.

    Args:
        cls: The class to check.
        *types: The types to check against.

    Returns:
        True if the class is a subclass of at least one type, False otherwise.
    """
    return IsSubclass(cls, types)

def Is[T](obj: T, types: Iterable[Type[T]]) -> bool:
    """Checks if an object's type is a subclass of any type in an iterable.

    Args:
        obj: The object to check.
        types: The types to check against.

    Returns:
        True if the object's type is a subclass of at least one type, False otherwise.
    """
    return IsSubclass(type(obj), types)
def IsOf[T](obj: T, *types: Type[T]) -> bool:
    """Checks if an object's type is a subclass of any type in variadic arguments.

    Args:
        obj: The object to check.
        *types: The types to check against.

    Returns:
        True if the object's type is a subclass of at least one type, False otherwise.
    """
    return Is(obj, types)

def Implements[T](cls: Type[T], types: Iterable[Type[T]]) -> bool:
    """Checks if a class implements all types in an iterable.

    Args:
        cls: The class to check.
        types: The types to check against.

    Returns:
        True if the class is a subclass of all types, False otherwise.
    """
    for type in types:
        if not issubclass(cls, type):
            return False

    return True
def ImplementsAll[T](cls: Type[T], *types: Type[T]) -> bool:
    """Checks if a class implements all types in variadic arguments.

    Args:
        cls: The class to check.
        *types: The types to check against.

    Returns:
        True if the class is a subclass of all types, False otherwise.
    """
    return Implements(cls, types)

def IsFrom[T](obj: T, types: Iterable[Type[T]]) -> bool:
    """Checks if an object's type implements all types in an iterable.

    Args:
        obj: The object to check.
        types: The types to check against.

    Returns:
        True if the object's type is a subclass of all types, False otherwise.
    """
    return Implements(type(obj), types)
def IsFromAll[T](obj: T, *types: Type[T]) -> bool:
    """Checks if an object's type implements all types in variadic arguments.

    Args:
        obj: The object to check.
        *types: The types to check against.

    Returns:
        True if the object's type is a subclass of all types, False otherwise.
    """
    return IsFrom(obj, types)

def AreInstances(type: type, *values: object) -> bool:
    """Checks if all values are instances of a type.

    Args:
        type: The type to check against.
        *values: The values to check.

    Returns:
        True if all values are instances of the type, False otherwise.
    """
    for value in values:
        if not isinstance(value, type):
            return False

    return True