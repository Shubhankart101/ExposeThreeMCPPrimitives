from __future__ import annotations

from dataclasses import asdict, dataclass


MAINTENANCE_TEMPLATE = (
    "Create a maintenance request for equipment {equipment_id}. "
    "Include observed symptoms and proposed inspection steps."
)


@dataclass(frozen=True)
class Equipment:
    equipment_id: str
    name: str
    available: bool


CATALOGUE = (
    Equipment("drill-01", "Cordless Drill", True),
    Equipment("meter-02", "Digital Multimeter", False),
    Equipment("camera-03", "Thermal Camera", True),
)


def catalogue_payload() -> list[dict]:
    return [asdict(item) for item in CATALOGUE]


def availability_payload(equipment_id: str) -> dict:
    for item in CATALOGUE:
        if item.equipment_id == equipment_id:
            return {
                "found": True,
                "equipment_id": item.equipment_id,
                "available": item.available,
            }
    return {
        "found": False,
        "equipment_id": equipment_id,
        "error": "equipment_not_found",
    }
