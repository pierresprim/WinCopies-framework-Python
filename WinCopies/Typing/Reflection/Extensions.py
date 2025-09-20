from __future__ import annotations

from abc import abstractmethod
from ast import Import, ImportFrom, Module, parse, walk
from importlib import import_module
from inspect import FrameInfo, Traceback, getframeinfo, getsource
from pkgutil import ModuleInfo, walk_packages
from sys import modules
from types import ModuleType, FrameType
from typing import Sequence, final

from WinCopies.Collections import Generator
from WinCopies.Collections.Extensions import IArray
from WinCopies.Collections.Abstraction.Collection import Array
from WinCopies.Typing import Reflection, IInterface, INullable, IDisposableInfo, IDisposableProvider, DisposableProvider, GetNullable, GetNullValue, GetDisposedError

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

class PackageInspector(IInterface):
    def __init__(self, package: ModuleType|str):
        super().__init__()

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

class IFrameInspector(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetFrame(self) -> FrameType:
        pass
    
    @abstractmethod
    def GetFileName(self) -> str:
        pass
    
    @abstractmethod
    def TryGetModuleName(self) -> INullable[str|None]:
        pass
    
    @abstractmethod
    def TryGetPackageName(self) -> str|None:
        pass
    
    @abstractmethod
    def TryGetModule(self) -> INullable[ModuleType|None]:
        pass
    
    @abstractmethod
    def TryGetPackage(self) -> ModuleType|None:
        pass
    
    @abstractmethod
    def IsInPackage(self, package: ModuleType|str) -> bool:
        pass
    
    @abstractmethod
    def GetFunctionName(self) -> str:
        pass
    @abstractmethod
    def GetLineNumber(self) -> int:
        pass
    
    @abstractmethod
    def HasModule(self) -> bool:
        pass
    @abstractmethod
    def HasPackage(self) -> bool:
        pass
    
    @abstractmethod
    def TryGetFunctionFullName(self) -> INullable[str|None]:
        pass
    
    @abstractmethod
    def TryIsMain(self) -> INullable[bool|None]:
        pass
    @abstractmethod
    def TryIsBuiltin(self) -> INullable[bool|None]:
        pass
class IDisposableFrameInspector(IFrameInspector, IDisposableInfo):
    def __init__(self):
        super().__init__()

class __IFrameInfo(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetFrame(self) -> FrameType:
        pass
    @abstractmethod
    def GetFileName(self) -> str:
        pass
    @abstractmethod
    def GetFunction(self) -> str:
        pass
    @abstractmethod
    def GetLineNumber(self) -> int:
        pass

@final
class __FrameInfo(__IFrameInfo):
    def __init__(self, frameInfo: FrameInfo):
        super().__init__()

        self.__frameInfo: FrameInfo = frameInfo
    
    def GetFrame(self) -> FrameType:
        return self.__frameInfo.frame
    def GetFileName(self) -> str:
        return self.__frameInfo.filename
    def GetFunction(self) -> str:
        return self.__frameInfo.function
    def GetLineNumber(self) -> int:
        return self.__frameInfo.lineno
@final
class __Traceback(__IFrameInfo, IDisposableInfo):
    def __init__(self, frame: FrameType, traceback: Traceback):
        super().__init__()

        self.__frame: FrameType = frame
        self.__traceback: Traceback = traceback
    
    def GetFrame(self) -> FrameType:
        return self.__frame
    def GetFileName(self) -> str:
        return self.__traceback.filename
    def GetFunction(self) -> str:
        return self.__traceback.function
    def GetLineNumber(self) -> int:
        return self.__traceback.lineno

@final
class __FrameInspector(IFrameInspector):
    def __init__(self, frameInfo: __IFrameInfo):
        super().__init__()

        self.__frameInfo: __IFrameInfo = frameInfo
    
    def GetFrame(self) -> FrameType:
        return self.__frameInfo.GetFrame()
    
    def GetFileName(self) -> str:
        return self.__frameInfo.GetFileName()
    
    def TryGetModuleName(self) -> INullable[str|None]:
        return Reflection.TryGetModuleNameFromFrame(self.GetFrame())
    
    def TryGetPackageName(self) -> str|None:
        return Reflection.TryGetPackageNameFromFrame(self.GetFrame())
    
    def TryGetModule(self) -> INullable[ModuleType|None]:
        module: INullable[ModuleType|None] = Reflection.TryGetModuleFromFrame(self.GetFrame())

        return GetNullable(Reflection.TryFindModuleFromFileName(self.__frameInfo.GetFileName())) if module.TryGetValue() is None else module
    
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
        return self.__frameInfo.GetFunction()
    def GetLineNumber(self) -> int:
        return self.__frameInfo.GetLineNumber()
    
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
    
    def TryIsMain(self) -> INullable[bool|None]:
        return Reflection.TryIsMain(self.GetFrame())
    def TryIsBuiltin(self) -> INullable[bool|None]:
        return Reflection.TryIsBuiltin(self.GetFrame())

def CreateFrameInspector(frameInfo: FrameInfo) -> IFrameInspector:
    return __FrameInspector(__FrameInfo(frameInfo))
def CreateFrameInspectorFromFrame(frame: FrameType) -> IFrameInspector:
    return __FrameInspector(__Traceback(frame, getframeinfo(frame)))

@final
class __DisposableFrameInspector(IDisposableInfo):
    def __init__(self, frame: FrameType):
        super().__init__()

        self.__frame: FrameType = frame
        self.__frameInspector: IFrameInspector|None = CreateFrameInspectorFromFrame(self.__frame)
    
    def IsDisposed(self) -> bool:
        return self.__frameInspector is None
    
    def GetFrameInspector(self) -> IFrameInspector:
        if self.__frameInspector is None or self.IsDisposed():
            raise GetDisposedError()
        
        return self.__frameInspector
    
    def Dispose(self) -> None:
        self.__frameInspector = None

        del self.__frame

class DisposableFrameInspector(IDisposableFrameInspector):
    def __init__(self, frame: FrameType):
        super().__init__()

        self.__frameInspector: IDisposableProvider[__DisposableFrameInspector] = DisposableProvider(__DisposableFrameInspector(frame))
    
    def __GetFrameInspector(self) -> IFrameInspector:
        return self.__frameInspector.GetItem().GetFrameInspector()
    
    def GetFrame(self) -> FrameType:
        return self.__GetFrameInspector().GetFrame()
    
    def GetFileName(self) -> str:
        return self.__GetFrameInspector().GetFileName()
    
    def TryGetModuleName(self) -> INullable[str|None]:
        return self.__GetFrameInspector().TryGetModuleName()
    
    def TryGetPackageName(self) -> str|None:
        return self.__GetFrameInspector().TryGetPackageName()
    
    def TryGetModule(self) -> INullable[ModuleType|None]:
        return self.__GetFrameInspector().TryGetModule()
    
    def TryGetPackage(self) -> ModuleType|None:
        return self.__GetFrameInspector().TryGetPackage()
    
    def IsInPackage(self, package: ModuleType|str) -> bool:
        return self.__GetFrameInspector().IsInPackage(package)
    
    def GetFunctionName(self) -> str:
        return self.__GetFrameInspector().GetFunctionName()
    def GetLineNumber(self) -> int:
        return self.__GetFrameInspector().GetLineNumber()
    
    def HasModule(self) -> bool:
        return self.__GetFrameInspector().HasModule()
    def HasPackage(self) -> bool:
        return self.__GetFrameInspector().HasPackage()
    
    def TryGetFunctionFullName(self) -> INullable[str|None]:
        return self.__GetFrameInspector().TryGetFunctionFullName()
    
    def TryIsMain(self) -> INullable[bool|None]:
        return self.__GetFrameInspector().TryIsMain()
    def TryIsBuiltin(self) -> INullable[bool|None]:
        return self.__GetFrameInspector().TryIsBuiltin()
    
    def Dispose(self) -> None:
        self.__frameInspector.Dispose()

class FrameHierarchy(IInterface):
    def __init__(self, inspector: IFrameInspector):
        super().__init__()

        self.__inspector: IFrameInspector = inspector
        self.__hierarchy: INullable[IArray[str]]|None = None
    
    def TryGetModuleName(self) -> str|None:
        return self.__inspector.TryGetModuleName().TryGetValue()
    def TryGetPackageName(self) -> str|None:
        return self.__inspector.TryGetPackageName()
    
    def TryIsMain(self) -> bool|None:
        return self.__inspector.TryIsMain().TryGetValue()
    def TryIsBuiltin(self) -> bool|None:
        return self.__inspector.TryIsBuiltin().TryGetValue()
    
    def GetFileName(self) -> str:
        return self.__inspector.GetFileName()
    
    def TryGetHierarchy(self) -> INullable[IArray[str]]:
        def tryGetModuleName(inspector: IFrameInspector) -> str|None:
            moduleName: INullable[str|None] = inspector.TryGetModuleName()

            return moduleName.TryGetValue()
        
        if self.__hierarchy is None:
            def tryGetHierarchy() -> INullable[IArray[str]]:
                moduleName: str|None = tryGetModuleName(self.__inspector)

                if moduleName is None:
                    return GetNullValue()
                
                hierarchy: Sequence[str] = moduleName.split('.')
                parent: str|None = None

                return GetNullable(Array[str]([parent for i in range(1, len(hierarchy)) if (parent := hierarchy[i]) in modules]))
            
            self.__hierarchy = tryGetHierarchy()
        
        return self.__hierarchy
    
    @staticmethod
    def CreateFromFrameInfo(frameInfo: FrameInfo) -> FrameHierarchy:
        return FrameHierarchy(CreateFrameInspector(frameInfo))

def GetFrameHierarchy(frameInfo: FrameInfo) -> FrameHierarchy:
    return FrameHierarchy.CreateFromFrameInfo(frameInfo)