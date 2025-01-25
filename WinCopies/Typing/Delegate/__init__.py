from typing import Callable

type Method = Callable[[], None]
type Function[T] = Callable[[], T]
type Predicate[T] = Callable[[T], bool]
type Converter[TIn, TOut] = Callable[[TIn], TOut]
type Selector[T] = Converter[T, T]