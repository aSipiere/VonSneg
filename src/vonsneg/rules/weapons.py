from abc import ABC
from dataclasses import dataclass, field


@dataclass
class BaseWeapon(ABC):
    name: str
    melee_inaccuracy_mod: int = 0
    shooting_save_mod: int = 0
    reroll_charge: bool = False
    can_shoot: callable = field(default=lambda state: True, repr=False)


@dataclass
class CloseCombatWeapon(BaseWeapon):
    name: str = "Close Combat Weapon"
    melee_inaccuracy_mod: int = -1
    reroll_charge: bool = True
    can_shoot: callable = field(default=lambda state: False, repr=False)


@dataclass
class BlackPowderWeapon(BaseWeapon):
    name: str = "Black Powder Weapon"
    can_shoot_func: callable = field(default=lambda state: not state.get("smoke", False), repr=False)


@dataclass
class MissileWeapon(BaseWeapon):
    name: str = "Missile Weapon"
    shooting_save_mod: int = -2


@dataclass
class PistolAndSabre(BaseWeapon):
    name: str = "Pistol & Sabre"
