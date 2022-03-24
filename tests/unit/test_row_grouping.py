from collections import OrderedDict

from screfinery.basestore import group_rows, group_init, group_rel_many_scalar, group_rel_many


def test_group_rows():
    data = [
        {
            "method_id": 1,
            "method_name": "Dinyx",
            "scope": "foo",
            "ore_id": 1,
            "ore_name": "Quant",
            "efficiency": 0.95,
            "duration": 60,
            "cost": 20,
        },
        {
            "method_id": 1,
            "method_name": "Dinyx",
            "scope": "bar",
            "ore_id": 2,
            "ore_name": "Aluminium",
            "efficiency": 0.97,
            "duration": 30,
            "cost": 20,
        },
        {
            "method_id": 2,
            "method_name": "Cormack",
            "scope": "zap",
            "ore_id": 1,
            "ore_name": "Quant",
            "efficiency": 0.87,
            "duration": 10,
            "cost": 80
        },
        {
            "method_id": 2,
            "method_name": "Cormack",
            "scope": "wusch",
            "ore_id": 2,
            "ore_name": "Aluminium",
            "efficiency": 0.87,
            "duration": 10,
            "cost": 80
        },
        {
            "method_id": 3,
            "method_name": "Foobar",
            "scope": None,
            "ore_id": None,
            "ore_name": None,
            "efficiency": None,
            "duration": None,
            "cost": None
        },
        {
            "method_id": 3,
            "method_name": "Foobar",
            "scope": None,
            "ore_id": None,
            "ore_name": None,
            "efficiency": None,
            "duration": None,
            "cost": None
        },
    ]
    expected = [
        {
            "method_id": 1,
            "method_name": "Dinyx",
            "scopes": ["foo", "bar"],
            "efficiencies": [
                {
                    "ore_id": 1,
                    "ore_name": "Quant",
                    "efficiency": 0.95,
                    "duration": 60,
                    "cost": 20,
                },
                {
                    "ore_id": 2,
                    "ore_name": "Aluminium",
                    "efficiency": 0.97,
                    "duration": 30,
                    "cost": 20,
                }
            ]
        },
        {
            "method_id": 2,
            "method_name": "Cormack",
            "scopes": ["zap", "wusch"],
            "efficiencies": [
                {
                    "ore_id": 1,
                    "ore_name": "Quant",
                    "efficiency": 0.87,
                    "duration": 10,
                    "cost": 80
                },
                {
                    "ore_id": 2,
                    "ore_name": "Aluminium",
                    "efficiency": 0.87,
                    "duration": 10,
                    "cost": 80
                }
            ]
        },
        {
            "method_id": 3,
            "method_name": "Foobar",
            "scopes": [],
            "efficiencies": []
        }
    ]
    rows_grouped = group_rows(
        group_init(lambda row: row["method_id"], "method_id", "method_name"),
        group_rel_many_scalar("scopes", "scope"),
        group_rel_many("efficiencies", "ore_id", "ore_name", "efficiency", "duration", "cost")
    )
    result = rows_grouped(data)
    assert result[0] == expected[0]
    assert result[1] == expected[1]
    assert result[2] == expected[2]