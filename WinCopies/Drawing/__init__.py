# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 14:21:00 2024

@author: Pierre Sprimont
"""

from abc import abstractmethod
from typing import final

from WinCopies import IInterface

class IPoint(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetX(self) -> int:
        pass
    @abstractmethod
    def GetY(self) -> int:
        pass

    def __str__(self):
        return f"{self.GetX()};{self.GetY()}"
class IPoint3D(IPoint):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Get2D(self) -> IPoint:
        pass
    
    @abstractmethod
    def GetZ(self) -> int:
        pass

    def __str__(self):
        return f"{super().__str__()};{self.GetZ()}"

@final
class Point(IPoint):
    @final
    class __Point(IPoint):
        def __init__(self, value: int):
            super().__init__()

            self.__value: int = value
        
        def GetX(self) -> int:
            return self.__value
        def GetY(self) -> int:
            return self.__value
    
    def __init__(self, x: int, y: int):
        super().__init__()

        self.__x: int = x
        self.__y: int = y
    
    @staticmethod
    def Create(x: int, y: int) -> IPoint:
        return Point.__Point(x) if x == y else Point(x, y)
    
    def GetX(self) -> int:
        return self.__x
    def GetY(self) -> int:
        return self.__y

@final
class Point3D(IPoint3D):
    def __init__(self, point: IPoint, z: int):
        super().__init__()

        self.__point: IPoint = point
        self.__z: int = z
    
    @staticmethod
    def Create(x: int, y: int, z: int) -> IPoint3D:
        return Point3D(Point.Create(x, y), z)
    
    def Get2D(self) -> IPoint:
        return self.__point
    
    def GetX(self) -> int:
        return self.Get2D().GetX()
    def GetY(self) -> int:
        return self.Get2D().GetY()
    def GetZ(self) -> int:
        return self.__z

class IRectangle(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetTopLeft(self) -> IPoint:
        pass
    @abstractmethod
    def GetBottomRight(self) -> IPoint:
        pass
    
    @final
    def GetX(self) -> int:
        return self.GetTopLeft().GetX()
    @final
    def GetY(self) -> int:
        return self.GetTopLeft().GetY()
    @final
    def GetHeight(self) -> int:
        return self.GetBottomRight().GetY()
    @final
    def GetWidth(self) -> int:
        return self.GetBottomRight().GetX()

@final
class Rectangle(IRectangle):
    def __init__(self, topLeft: Point, bottomRight: Point):
        super().__init__()
        
        self.__topLeft: Point = topLeft
        self.__bottomRight: Point = bottomRight
    
    @staticmethod
    def FromCoordinates(x: int, y: int, width: int, height: int) -> IRectangle:
        return Rectangle(Point(x, y), Point(width, height))
    
    def GetTopLeft(self) -> IPoint:
        return self.__topLeft
    def GetBottomRight(self) -> IPoint:
        return self.__bottomRight