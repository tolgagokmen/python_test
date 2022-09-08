import json
from datetime import datetime
from functools import reduce

import pytest

def to_date(dateItem):
    df = '%Y-%m-%d %H:%M:%S'
    return datetime.strptime(dateItem['timestamp'], df)


class EventManager:

    @classmethod
    def from_dict(cls, events_dict: dict):
        """
        This class is going to be our starting point. We want to parse the events from a dictionary here.
        """
        res = {}
        for item in sorted(events_dict["events"], key=lambda x: to_date(x)):
            res.setdefault(item['patient_id'], {"events": []})
            res.get(item['patient_id'])["events"].append(item)
        res = {"patient_map": res}

        for k, v in res["patient_map"].items():
            sign_in_in_minutes = 0
            for stage in {"sign_in", "time_out", "sign_out"}:
                sign_in_in_minutes += reduce(lambda x, y: (to_date(y) - to_date(x)).seconds / 60,
                                             filter(lambda s: s["stage_id"] == stage, v["events"]))
            v["surgery_duration_in_minutes"] = sign_in_in_minutes
        return res


@pytest.fixture(
    name="event_manager"
)
def make_event_manager():
    with open("events.json") as f:
        return EventManager.from_dict(
            json.load(f)
        )


class TestCase:
    def test_patient_map(self, event_manager):
        """
        There are 3 distinct patients in the data so our patient_map should be length 3.
        """
        assert len(event_manager["patient_map"]) == 3

    @pytest.mark.parametrize(
        "patient_id",
        [
            "patient_1",
            "patient_2",
            "patient_3",
        ]
    )
    def test_events(
            self,
            event_manager,
            patient_id
    ):
        """
        I want to be able to index the event_manager to get a patient object. I know that each
        patient should have 6 events associated with them and also that those events ought to
        be ordered by when they occurred.
        """
        patient = event_manager["patient_map"][patient_id]
        assert len(patient["events"]) == 6
        for i in range(len(patient["events"]) - 1):
            datetime_format = '%Y-%m-%d %H:%M:%S'
            datetime_object1 = datetime.strptime(patient["events"][i]["timestamp"], datetime_format)
            datetime_object2 = datetime.strptime(patient["events"][i + 1]["timestamp"], datetime_format)
            assert datetime_object1 <= datetime_object2

    @pytest.mark.parametrize(
        "patient_id, surgery_time",
        [
            ("patient_1", 40),
            ("patient_2", 39),
            ("patient_3", 45),
        ]
    )
    def test_surgery_duration(
            self,
            event_manager,
            patient_id,
            surgery_time
    ):
        """
        Finally I want to look at those events and compute how long each surgery took.
        """

        assert event_manager["patient_map"][patient_id]["surgery_duration_in_minutes"] == surgery_time
