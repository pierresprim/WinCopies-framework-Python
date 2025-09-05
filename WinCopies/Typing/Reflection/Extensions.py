from __future__ import annotations

from ast import Import, ImportFrom, Module, parse, walk
from importlib import import_module
from inspect import FrameInfo, getsource, stack
from pkgutil import ModuleInfo, walk_packages
from types import ModuleType, FrameType

from WinCopies.Collections import Generator
from WinCopies.Typing import InvalidOperationError, INullable, Reflection, GetNullable

def ImportModule(package: ModuleType|str) -> ModuleType:
    return import_module(package) if isinstance(package, str) else package

def EnumerateSubmodules(package: ModuleType|str, includePrivate: bool = False) -> Generator[ModuleInfo]:
    def enumerateSubmodules(package: ModuleType) -> Generator[ModuleInfo]:
        for moduleInfo in walk_packages(package.__path__, package.__name__ + '.'):
            if includePrivate or not moduleInfo.name.split('.')[-1].startswith('_'):
                yield moduleInfo
    
    return enumerateSubmodules(ImportModule(package))

def TryEnumerateImports(module: ModuleType) -> Generator[str]|None:
    try:
        source: str = getsource(module)
        tree: Module = parse(source)
        
        for node in walk(tree):
            if isinstance(node, Import):
                for alias in node.names:
                    yield alias.name
            
            elif isinstance(node, ImportFrom):
                moduleName: str = node.module or ''

                for alias in node.names:
                    yield f"{moduleName}.{alias.name}"
    
    except (OSError, TypeError):
        return None

def TryImportsFromPackage(module: ModuleType, packageName: str) -> bool|None:
    imports: Generator[str]|None = TryEnumerateImports(module)

    if imports is None:
        return None

    return any(imp.startswith(packageName) for imp in imports)

class PackageInspector:
    def __init__(self, package: ModuleType|str):
        self.__package: ModuleType = ImportModule(package)
    
    def GetName(self) -> str:
        return self.__package.__name__
    
    def ContainsModule(self, module: ModuleType) -> bool:
        return Reflection.IsSubmoduleFromNames(Reflection.GetModuleName(module), self.GetName())
    
    def EnumerateSubmodules(self, includePrivate: bool = False):
        return EnumerateSubmodules(self.__package, includePrivate)
    
    def TryFindModule(self, name: str) -> ModuleType|None:
        fullName: str = f"{self.GetName()}.{name}"

        try:
            return import_module(fullName)
        except ImportError:
            return None

class FrameInspector:
    def __init__(self, frameInfo: FrameInfo):
        self.__frameInfo: FrameInfo = frameInfo
    
    def GetFrame(self) -> FrameType:
        return self.__frameInfo.frame
    
    def GetFileName(self) -> str:
        return self.__frameInfo.filename
    
    def TryGetModuleName(self) -> INullable[str|None]:
        return Reflection.TryGetModuleNameFromFrame(self.GetFrame())
    
    def TryGetPackageName(self) -> str|None:
        Reflection.TryGetPackageNameFromFrame(self.GetFrame())
    
    def TryGetModule(self) -> INullable[ModuleType|None]:
        module: INullable[ModuleType|None] = Reflection.TryGetModuleFromFrame(self.GetFrame())

        return GetNullable(Reflection.TryFindModuleFromFrameInfo(self.__frameInfo)) if module.TryGetValue() is None else module
    
    def TryGetPackage(self) -> ModuleType|None:
        packageName: str|None = self.TryGetPackageName()

        if packageName is None:
            return None

        try:
            return import_module(packageName)
        except ImportError:
            return None
    
    def IsInPackage(self, package: ModuleType|str) -> bool:
        return Reflection.TryIsModuleInPackageFromFrame(self.GetFrame(), package)
    
    def GetFunctionName(self) -> str:
        return self.__frameInfo.function
    def GetLineNumber(self) -> int:
        return self.__frameInfo.lineno
    
    def HasModule(self) -> bool:
        return self.TryGetModule().TryGetValue() is not None
    def HasPackage(self) -> bool:
        return self.TryGetPackage() is not None
    
    def TryGetFunctionFullName(self) -> INullable[str|None]:
        moduleName: INullable[str|None] = self.TryGetModuleName()

        if moduleName.HasValue():
            value: str|None = moduleName.TryGetValue()

            return GetNullable(None if value is None else f"{value}.{self.GetFunctionName()}")
        
        return moduleName

def EnumerateFromCallStack() -> Generator[FrameInfo]:
    for frame in stack():
        yield frame

def __CheckCallerPackage(targetPackage: ModuleType|str, index: int) -> bool:
    # Get caller's frame (index 1 in stack)
    inspector: FrameInspector = FrameInspector(stack()[index])
    
    return inspector.IsInPackage(targetPackage)

def CheckCallerPackage(targetPackage: ModuleType|str) -> bool:
    return __CheckCallerPackage(targetPackage, 1)
def EnsureCallerPackage(targetPackage: ModuleType|str) -> None:
    if not __CheckCallerPackage(targetPackage, 2):
        raise InvalidOperationError(f"This function can only be called from {targetPackage}.")