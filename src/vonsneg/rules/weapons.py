from abc import ABC
from dataclasses import dataclass, field


@dataclass
class BaseWeapon(ABC):
    name: str
    melee_inaccuracy_mod: int = 0
    shooting_save_mod: int = 0
    reroll_charge: bool = False
    can_shoot: callable = field(default=lambda: True, repr=False)


@dataclass
class CloseCombatWeapon(BaseWeapon):
    name: str = "Close Combat Weapon"
    melee_inaccuracy_mod: int = -1
    reroll_charge: bool = True
    can_shoot: callable = field(default=lambda: False, repr=False)


@dataclass
class BlackPowderWeapon(BaseWeapon):
    name: str = "Black Powder Weapon"

    def can_shoot(self, unit_state=None):
        """Check if the weapon can shoot.
        Black powder weapons cannot shoot if the unit has a powder smoke token.

        :param unit_state: Optional state dict containing 'smoke' key
        :return: True if can shoot, False if blocked by powder smoke
        """
        if unit_state and unit_state.get("smoke", False):
            return False
        return True


@dataclass
class MissileWeapon(BaseWeapon):
    name: str = "Missile Weapon"
    shooting_save_mod: int = -2
    can_shoot: callable = field(default=lambda: True, repr=False)


@dataclass
class OldMissileWeapon(BaseWeapon):
    name: str = "Old Missile Weapon"
    shooting_save_mod: int = -1
    can_shoot: callable = field(default=lambda: True, repr=False)


@dataclass
class PistolAndSabre(BaseWeapon):
    name: str = "Pistol & Sabre"
    can_shoot: callable = field(default=lambda: True, repr=False)
