"""
Unit tests for WinCopies.Serialization.JSON module.
"""

import unittest

from WinCopies.Serialization.JSON import Event, EventNames

class TestEventNames(unittest.TestCase):
    def test_every_event_name_converts_to_its_event(self) -> None:
        expected: dict[EventNames, Event] = {
            EventNames.StartMap: Event.StartMap,
            EventNames.EndMap: Event.EndMap,
            EventNames.StartArray: Event.StartArray,
            EventNames.EndArray: Event.EndArray,
            EventNames.MapKey: Event.MapKey,
            EventNames.Null: Event.NullValue,
            EventNames.Boolean: Event.Boolean,
            EventNames.Integer: Event.Integer,
            EventNames.Double: Event.Double,
            EventNames.Number: Event.Number,
            EventNames.String: Event.String}

        self.assertEqual(len(expected), len(EventNames))

        for name, event in expected.items():
            with self.subTest(name=name): self.assertIs(EventNames.TryConvertToEvent(name.value), event)

    def test_unknown_event_name_converts_to_none(self) -> None:
        self.assertIsNone(EventNames.TryConvertToEvent("unknown"))

if __name__ == '__main__': unittest.main()