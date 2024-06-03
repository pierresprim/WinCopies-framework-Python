# -*- coding: utf-8 -*-
"""
Created on Thu May 30 07:37:00 2024

@author: Pierre Sprimont
"""

from typing import final
import os
from WinCopies import Delegates

def ProcessDirEntries(path: str, func: callable) -> bool|None:
    if os.path.exists(path):
        with os.scandir(path) as paths:
            return True if func(paths) else None
    
    return False

def ScanDir(path: str, func: callable) -> bool|None:
    def scanDir(paths) -> bool:
        nonlocal func

        for entry in paths:
            if not func(entry):
                return False
        
        return True

    return ProcessDirEntries(path, scanDir)

def ParseDir(path: str, predicate: callable, action: callable) -> bool|None:
    return ScanDir(path, Delegates.GetPredicateAction(predicate, action))

def ScanDirEntries(path: str, action: callable):
    def scanDirEntries(paths) -> bool:
        nonlocal action

        for entry in paths:
            action(entry)
        
        return True
    
    ProcessDirEntries(path, scanDirEntries)

def ParseDirEntries(path: str, predicate: callable, action: callable) -> bool|None:
    
    @final
    class Parser:
        def __init__(self, predicate: callable, action: callable):
            self.__predicate: callable = predicate
            self.__action: callable = action
            self.__func: callable|None = None
            self.__result: bool|None = None
        
        def __ScanDir(self, entry: os.DirEntry):
            if self.__predicate(entry):
                self.__action(entry)
        
        def __TryScanDir(self, entry: os.DirEntry):
            if self.__predicate(entry):
                self.__action(entry)
            
            else:
                self.__func = self.__ScanDir

                self.__result = False
    
        def ParseDirEntries(self, paths) -> bool:
            self.__func = self.__TryScanDir
            self.__result = True

            for entry in paths:
                self.__func(entry)
            
            return self.__result
        
    return ProcessDirEntries(path, Parser(predicate, action).ParseDirEntries)