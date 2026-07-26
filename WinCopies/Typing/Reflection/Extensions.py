from __future__ import annotations

from abc import abstractmethod
from ast import Import, ImportFrom, Module, parse, walk
from collections.abc import Iterable, Sequence
from enum import Enum
from importlib import import_module
from inspect import FrameInfo, Traceback, getframeinfo, getsource, getmembers, isfunction, ismethod
from pkgutil import ModuleInfo as ModuleInfoBase, walk_packages
from sys import modules
from types import ModuleType, FrameType, FunctionType, MethodType
from typing import Protocol, Type, final

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction.Collection import Array
from WinCopies.Collections.Extensions import IArray
from WinCopies.Collections.Util import GetLastItem
from WinCopies.String import TrySplit, SplitFromLast
from WinCopies.Typing import INullable, IDisposableInfo, IDisposableProvider, DisposableProvider, GetNullable, GetNullValue, TryGetValue, GetDisposedError
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import KeyValuePair
from WinCopies.Typing.Reflection import GetModuleName, TryGetModuleNameFromFrame, TryGetPackageNameFromFrame, TryFindModuleFromFileName, TryGetModuleFromFrame, IsSubmoduleFromNames, TryIsModuleInPackageFromFrame, TryIsMain, TryIsBuiltin

def GetFunctions(t: type) -> Sequence[tuple[str, FunctionType]]:
    return getmembers(t, isfunction)
def GetMethods(obj: object) -> Sequence[tuple[str, MethodType]]:
    return getmembers(obj, ismethod)

def _EnumerateMembers[T](members: Iterable[tuple[str, T]]) -> Generator[KeyValuePair[str, T]]:
    return (KeyValuePair(member_name, member) for (member_name, member) in members)

def EnumerateFunctions(t: type) -> Generator[KeyValuePair[str, FunctionType]]:
    return _EnumerateMembers(GetFunctions(t))
def EnumerateMethods(obj: object) -> Generator[KeyValuePair[str, MethodType]]:
    return _EnumerateMembers(GetMethods(obj))

def ImportModule(package: ModuleType|str) -> ModuleType:
    return import_module(package) if isinstance(package, str) else package

def EnumerateSubmodules(package: ModuleType|str, includePrivate: bool = False) -> Generator[ModuleInfoBase]:
    def enumerateSubmodules(package: ModuleType) -> Generator[ModuleInfoBase]:
        for moduleInfo in walk_packages(package.__path__, package.__name__ + '.'):
            if includePrivate or not moduleInfo.name.split('.')[-1].startswith('_'): yield moduleInfo
    
    return enumerateSubmodules(ImportModule(package))

def TryEnumerateImports(module: ModuleType) -> Generator[str]|None:
    def enumerate() -> Generator[str]:
        source: str = getsource(module)
        tree: Module = parse(source)
        
        for node in walk(tree):
            if isinstance(node, Import):
                for alias in node.names: yield alias.name
            
            elif isinstance(node, ImportFrom):
                moduleName: str = node.module or ''

                for alias in node.names: yield f"{moduleName}.{alias.name}"
    
    try: return enumerate()
    except (OSError, TypeError): return None

def TryImportsFromPackage(module: ModuleType, packageName: str) -> bool|None:
    imports: Generator[str]|None = TryEnumerateImports(module)

    return None if imports is None else any(imp.startswith(packageName) for imp in imports)

class LoaderProtocol(Protocol):
    def load_module(self, fullname: str, /) -> ModuleType: ...

class ModuleInfo(Abstract):
    def __init__(self, module: ModuleType|str) -> None:
        super().__init__()

        self.__module: ModuleType = ImportModule(module)
    
    @final
    def SplitFromLast(self) -> Sequence[str]:
        return SplitFromLast(self.GetPath(), '.')

    @final
    def _GetModule(self) -> ModuleType:
        return self.__module

    @final
    def GetPath(self) -> str:
        return self._GetModule().__name__

    @final
    def GetPackageName(self) -> str|None:
        path: Sequence[str]|None = TrySplit(self.GetPath(), '.')

        return None if path is None or len(path) < 2 else path[0]
    
    @final
    def GetDirectory(self) -> str:
        return self.SplitFromLast()[0]
    
    @final
    def GetName(self) -> str:
        return GetLastItem(self.SplitFromLast())
    
    @final
    def TryGetFile(self) -> str|None:
        return self._GetModule().__file__
    
    @final
    def GetLoader(self) -> LoaderProtocol|None:
        return self._GetModule().__loader__
    
    @final
    def TryGetDoc(self) -> str|None:
        return self._GetModule().__doc__
    
    def ContainsModule(self, module: ModuleType|ModuleInfo) -> bool: return IsSubmoduleFromNames(GetModuleName(module if isinstance(module, ModuleType) else module._GetModule()), self.GetPath())
    
    def EnumerateSubmodules(self, includePrivate: bool = False) -> Generator[ModuleInfoBase]: return EnumerateSubmodules(self.__module, includePrivate)
    
    def TryFindModule(self, name: str) -> ModuleType|None:
        fullName: str = f"{self.GetPath()}.{name}"

        try: return import_module(fullName)
        except ImportError: return None

class IFrameInspector(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetFrame(self) -> FrameType:
        ...
    
    @abstractmethod
    def GetFileName(self) -> str:
        ...
    
    @abstractmethod
    def TryGetModuleName(self) -> INullable[str]|None:
        ...
    
    @abstractmethod
    def TryGetPackageName(self) -> str|None:
        ...
    
    @abstractmethod
    def TryGetModule(self) -> ModuleType|None:
        ...
    
    @abstractmethod
    def TryGetPackage(self) -> ModuleType|None:
        ...
    
    @abstractmethod
    def IsInPackage(self, package: ModuleType|str) -> bool:
        ...
    
    @abstractmethod
    def GetFunctionName(self) -> str:
        ...
    @abstractmethod
    def GetLineNumber(self) -> int:
        ...
    
    @abstractmethod
    def HasModule(self) -> bool:
        ...
    @abstractmethod
    def HasPackage(self) -> bool:
        ...
    
    @abstractmethod
    def TryGetFunctionFullName(self) -> INullable[str]|None:
        ...
    
    @abstractmethod
    def TryIsMain(self) -> INullable[bool]|None:
        ...
    @abstractmethod
    def TryIsBuiltin(self) -> INullable[bool]|None:
        ...
class IDisposableFrameInspector(IFrameInspector, IDisposableInfo):
    def __init__(self) -> None: super().__init__()

class _IFrameInfo(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetFrame(self) -> FrameType:
        ...
    @abstractmethod
    def GetFileName(self) -> str:
        ...
    @abstractmethod
    def GetFunction(self) -> str:
        ...
    @abstractmethod
    def GetLineNumber(self) -> int:
        ...

@final
class __FrameInfo(Abstract, _IFrameInfo):
    def __init__(self, frameInfo: FrameInfo) -> None:
        super().__init__()

        self.__frameInfo: FrameInfo = frameInfo
    
    def GetFrame(self) -> FrameType: return self.__frameInfo.frame
    def GetFileName(self) -> str: return self.__frameInfo.filename
    def GetFunction(self) -> str: return self.__frameInfo.function
    def GetLineNumber(self) -> int: return self.__frameInfo.lineno
@final
class __Traceback(Abstract, _IFrameInfo, IDisposableInfo):
    class _IHandle(_IFrameInfo):
        def __init__(self) -> None: super().__init__()
        
        @abstractmethod
        def IsDisposed(self) -> bool:
            ...
        
        @abstractmethod
        def Dispose(self) -> __Traceback._IHandle:
            ...
    
    @final
    class _NullHandle(Abstract, _IHandle):
        def __init__(self) -> None: super().__init__()
        
        def IsDisposed(self) -> bool: return True

        def GetFrame(self) -> FrameType: raise GetDisposedError()
        def GetFileName(self) -> str: raise GetDisposedError()
        def GetFunction(self) -> str: raise GetDisposedError()
        def GetLineNumber(self) -> int: raise GetDisposedError()
        
        def Dispose(self) -> __Traceback._IHandle: return self
    @final
    class _Handle(Abstract, _IHandle):
        def __init__(self, frame: FrameType, traceback: Traceback) -> None:
            super().__init__()

            self.__frame: FrameType = frame
            self.__traceback: Traceback = traceback
        
        def IsDisposed(self) -> bool: return False

        def GetFrame(self) -> FrameType: return self.__frame
        def GetFileName(self) -> str: return self.__traceback.filename
        def GetFunction(self) -> str: return self.__traceback.function
        def GetLineNumber(self) -> int: return self.__traceback.lineno
        
        def Dispose(self) -> __Traceback._IHandle:
            del self.__traceback

            return __Traceback._NullHandle()
    
    def __init__(self, frame: FrameType, traceback: Traceback) -> None:
        super().__init__()

        self.__handle: __Traceback._IHandle = __Traceback._Handle(frame, traceback)
    
    def IsDisposed(self) -> bool: return self.__handle.IsDisposed()
    
    def GetFrame(self) -> FrameType: return self.__handle.GetFrame()
    def GetFileName(self) -> str: return self.__handle.GetFileName()
    def GetFunction(self) -> str: return self.__handle.GetFunction()
    def GetLineNumber(self) -> int: return self.__handle.GetLineNumber()
    
    def Dispose(self) -> None: self.__handle = self.__handle.Dispose()

@final
class __FrameInspector(Abstract, IFrameInspector):
    def __init__(self, frameInfo: _IFrameInfo) -> None:
        super().__init__()

        self.__frameInfo: _IFrameInfo = frameInfo
    
    def GetFrame(self) -> FrameType: return self.__frameInfo.GetFrame()
    
    def GetFileName(self) -> str: return self.__frameInfo.GetFileName()
    
    def TryGetModuleName(self) -> INullable[str]|None: return TryGetModuleNameFromFrame(self.GetFrame())
    
    def TryGetPackageName(self) -> str|None: return TryGetPackageNameFromFrame(self.GetFrame())
    
    def TryGetModule(self) -> ModuleType|None:
        def getResult() -> ModuleType|None: return TryFindModuleFromFileName(self.__frameInfo.GetFileName())
        
        module: INullable[ModuleType]|None = TryGetModuleFromFrame(self.GetFrame())

        if module is None: return getResult()
        
        result: ModuleType|None = module.TryGetValue()

        if result is None: return getResult()
        
        return result
    
    def TryGetPackage(self) -> ModuleType|None:
        packageName: str|None = self.TryGetPackageName()

        if packageName is None: return None

        try: return import_module(packageName)
        except ImportError: return None
    
    def IsInPackage(self, package: ModuleType|str) -> bool:
        return TryIsModuleInPackageFromFrame(self.GetFrame(), package)
    
    def GetFunctionName(self) -> str:
        return self.__frameInfo.GetFunction()
    def GetLineNumber(self) -> int:
        return self.__frameInfo.GetLineNumber()
    
    def HasModule(self) -> bool:
        return self.TryGetModule() is not None
    def HasPackage(self) -> bool:
        return self.TryGetPackage() is not None
    
    def TryGetFunctionFullName(self) -> INullable[str]|None:
        moduleName: INullable[str]|None = self.TryGetModuleName()

        if moduleName is None: return None

        value: str|None = moduleName.TryGetValue()

        return GetNullValue() if value is None else GetNullable(f"{value}.{self.GetFunctionName()}")
    
    def TryIsMain(self) -> INullable[bool]|None:
        return TryIsMain(self.GetFrame())
    def TryIsBuiltin(self) -> INullable[bool]|None:
        return TryIsBuiltin(self.GetFrame())

def CreateFrameInspector(frameInfo: FrameInfo) -> IFrameInspector:
    return __FrameInspector(__FrameInfo(frameInfo))
def CreateFrameInspectorFromFrame(frame: FrameType) -> IFrameInspector:
    return __FrameInspector(__Traceback(frame, getframeinfo(frame)))

@final
class __DisposableFrameInspector(Abstract, IDisposableInfo):
    def __init__(self, frame: FrameType) -> None:
        super().__init__()

        self.__frame: FrameType = frame
        self.__frameInspector: IFrameInspector|None = CreateFrameInspectorFromFrame(self.__frame)
    
    def IsDisposed(self) -> bool: return self.__frameInspector is None
    
    def GetFrameInspector(self) -> IFrameInspector:
        if self.__frameInspector is None or self.IsDisposed(): raise GetDisposedError()
        
        return self.__frameInspector
    
    def Dispose(self) -> None:
        self.__frameInspector = None

        del self.__frame

class DisposableFrameInspector(Abstract, IDisposableFrameInspector):
    def __init__(self, frame: FrameType) -> None:
        super().__init__()

        self.__frameInspector: IDisposableProvider[__DisposableFrameInspector] = DisposableProvider(__DisposableFrameInspector(frame))
    
    def __GetFrameInspector(self) -> IFrameInspector:
        return self.__frameInspector.GetItem().GetFrameInspector()
    
    def GetFrame(self) -> FrameType: return self.__GetFrameInspector().GetFrame()
    
    def GetFileName(self) -> str: return self.__GetFrameInspector().GetFileName()
    
    def TryGetModuleName(self) -> INullable[str]|None:
        return self.__GetFrameInspector().TryGetModuleName()
    
    def TryGetPackageName(self) -> str|None: return self.__GetFrameInspector().TryGetPackageName()
    
    def TryGetModule(self) -> ModuleType|None: return self.__GetFrameInspector().TryGetModule()
    
    def TryGetPackage(self) -> ModuleType|None: return self.__GetFrameInspector().TryGetPackage()
    
    def IsInPackage(self, package: ModuleType|str) -> bool: return self.__GetFrameInspector().IsInPackage(package)
    
    def GetFunctionName(self) -> str: return self.__GetFrameInspector().GetFunctionName()
    def GetLineNumber(self) -> int: return self.__GetFrameInspector().GetLineNumber()
    
    def HasModule(self) -> bool: return self.__GetFrameInspector().HasModule()
    def HasPackage(self) -> bool: return self.__GetFrameInspector().HasPackage()
    
    def TryGetFunctionFullName(self) -> INullable[str]|None: return self.__GetFrameInspector().TryGetFunctionFullName()
    
    def TryIsMain(self) -> INullable[bool]|None: return self.__GetFrameInspector().TryIsMain()
    def TryIsBuiltin(self) -> INullable[bool]|None: return self.__GetFrameInspector().TryIsBuiltin()
    
    def Dispose(self) -> None: self.__frameInspector.Dispose()

class FrameHierarchy(Abstract):
    def __init__(self, inspector: IFrameInspector) -> None:
        super().__init__()

        self.__inspector: IFrameInspector = inspector
        self.__hierarchy: INullable[IArray[str]]|None = None
    
    def TryGetModuleName(self) -> str|None:
        return TryGetValue(self.__inspector.TryGetModuleName())
    def TryGetPackageName(self) -> str|None:
        return self.__inspector.TryGetPackageName()
    
    def TryIsMain(self) -> bool|None:
        return TryGetValue(self.__inspector.TryIsMain())
    def TryIsBuiltin(self) -> bool|None:
        return TryGetValue(self.__inspector.TryIsBuiltin())
    
    def GetFileName(self) -> str:
        return self.__inspector.GetFileName()
    
    def TryGetHierarchy(self) -> INullable[IArray[str]]:
        def tryGetModuleName(inspector: IFrameInspector) -> str|None:
            moduleName: INullable[str]|None = inspector.TryGetModuleName()

            return TryGetValue(moduleName)
        
        if self.__hierarchy is None:
            def tryGetHierarchy() -> INullable[IArray[str]]:
                moduleName: str|None = tryGetModuleName(self.__inspector)

                if moduleName is None: return GetNullValue()
                
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

class MemberKind(Enum):
    Null = 0
    Field = 1
    Function = 2
    Method = 3

class ITypeInfo(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetType(self) -> type:
        ...

    @abstractmethod
    def GetFunctions(self) -> IArray[IFunctionInfo]:
        ...

class IMemberInfo(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetName(self) -> str:
        ...
    
    @abstractmethod
    def GetKind(self) -> MemberKind:
        ...

    @abstractmethod
    def GetType(self) -> ITypeInfo:
        ...

class IFunctionInfo(IMemberInfo):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetKind(self) -> MemberKind: return MemberKind.Function
    
    @abstractmethod
    def Call(self, obj: object, *args: object, **kwargs: object) -> object:
        ...
class IMethodInfo(IMemberInfo):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetKind(self) -> MemberKind: return MemberKind.Method
    
    @abstractmethod
    def Call(self, *args: object, **kwargs: object) -> object:
        ...

@final
class _TypeUpdater[T](ValueFunctionUpdater[IArray[IFunctionInfo]]):
    def __init__(self, t: TypeInfo[T], updater: Method[IFunction[IArray[IFunctionInfo]]]) -> None:
        super().__init__(updater)

        self.__type: TypeInfo[T] = t
    
    def _GetValue(self) -> IArray[IFunctionInfo]:
        return Array[IFunctionInfo](_Function(func.GetValue(), self.__type) for func in EnumerateFunctions(self.__type.GetType()))

class TypeInfo[T](Abstract, ITypeInfo):
    def __init__(self, type: Type[T]) -> None:
        def update(func: IFunction[IArray[IFunctionInfo]]) -> None: self.__functions = func
        
        super().__init__()

        self.__type: Type[T] = type
        self.__functions: IFunction[IArray[IFunctionInfo]] = _TypeUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def GetType(self) -> Type[T]: return self.__type
    
    @final
    def GetFunctions(self) -> IArray[IFunctionInfo]: return self.__functions.GetValue()

class _Member[T](Abstract, IMemberInfo):
    def __init__(self, member: T, t: ITypeInfo) -> None:
        super().__init__()

        self.__member: T = member
        self.__type: ITypeInfo = t
    
    @final
    def _GetMember(self) -> T:
        return self.__member
    
    def GetType(self) -> ITypeInfo: return self.__type

@final
class _Function(_Member[FunctionType], IFunctionInfo):
    def __init__(self, member: FunctionType, t: ITypeInfo) -> None:
        super().__init__(member, t)
    
    def GetName(self) -> str: return self._GetMember().__name__
    
    def Call(self, obj: object, *args: object, **kwargs: object) -> object: return self._GetMember()(obj, *args, **kwargs)