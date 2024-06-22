def Replace(string: str, esc: str, newEsc: str, *args: str) -> str:
    string = string.replace(esc + esc, esc)
    
    for arg in args:
        
        string = string.replace(esc + arg, newEsc + arg)
    
    return string