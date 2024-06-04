# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 11:47:00 2024

@author: Pierre Sprimont
"""
import os

from WinCopies import DualValueNullableBool

def TryGetExtensionFromArray(entry) -> str|None:
    return entry[1] if len(entry) > 1 else None

def TryGetExtension(name: str) -> str|None:
    return TryGetExtensionFromArray(os.path.splitext(name))

def GetExtensionFromArray(entry) -> str:
    result: str|None = TryGetExtensionFromArray(entry)
    
    return '' if result is None else result

def GetExtension(name: str) -> str:
    result: str|None = TryGetExtension(name)
    
    return '' if result is None else result

def TryCreateDirectory(directory: str) -> bool|None:
    try:
        if os.path.exists(directory):
            return False
    
        os.mkdir(directory)

        return True
    
    except FileExistsError:
        return None

def TryCreateSubdirectory(directory: str, subdirectory: str) -> DualValueNullableBool[str]:
    directory = os.path.join(directory, subdirectory)

    return DualValueNullableBool(directory, TryCreateDirectory(directory))