# -*- coding: utf-8 -*-
"""
Created on Fri May 26 14:04:01 2023

@author: Pierre Sprimont
"""

from WinCopies import SequenceGenerator, AskConfirmation, DoProcess, AskInt, TryMessage
from WinCopies.IO.Stream import File, FileMode, FileType

def process() -> None:
    def onFileError(e: Exception) -> bool:
        return AskConfirmation("Continue?")

    fileInitializer: callable = File.GetFileInitializer(FileMode.Write, FileType.Text, onFileError)

    pattern: str = input("Enter a pattern: ")
        
    def askValue(valueName: str, predicate: callable) -> int:
        
        return AskInt("Enter the " + valueName + ": ", predicate)
    
    start: int = askValue("start", lambda value: value <= 0)
    count: int = askValue("count", lambda value: value < 0)
    
    if AskConfirmation("Proceed?"):
        file: File|None = fileInitializer()

        if file is None:
            return

        sequenceGenerator: SequenceGenerator = SequenceGenerator(pattern, start, count)
        
        def enumerate() -> None:
            writer: callable
            
            def write(string: str) -> None:
                nonlocal writer
                
                file.Write(string)
                
                writer = lambda string: file.Write("\n" + string)
            
            writer = write
        
            for string in sequenceGenerator:
                print(string)
                
                writer(string)
        
        TryMessage(enumerate, print)
        
        file.Close()

DoProcess(process)