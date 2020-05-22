"""Representation of the abstract status of the player.
"""

import enum


@enum.unique
class Prayer(enum.Enum):
    """
    Prayers obtained at the altars of Apollo.
    """

    DIVINE_RESTORATION = 0
    FORTITUDE = 1
    BLOODLUST = 2
    MIGHTY_BASH = 3
    SWEEPING_BASH = 4
    SPINNING_BASH = 5
    QUICK_BASH = 6
    GREATER_THROW = 7
    GREATER_THROW_II = 8
    GREATER_ENERGY = 9
    GREATER_ENERGY_II = 10
    DEEP_LUNGE = 11
    PATIENCE = 12
    SURGE = 13
    REGENERATION = 14
    WINGED_SANDALS = 15
    STAGGERING_LEAP = 16


class PlayerAttributes:  # pylint: disable=R0903
    """Representation of the attributes of the player, which will determine
    the result of its actions.

    Attributes
    ----------
    maximum_health : int
        Maximum number of hearts (capped to 8 in the game).
    maximum_energy : int
        Maximum energy amount.
    knockback_distance : int
        Knockback distance in tiles for bash moves.
    cooldown : int
        Number of turns to wait after having used a bash move.
    throw_distance : int
        Radius of the reachable circle when throwing the spear.
    leap_distance : int
        Radius of the reachable circle when leaping.

    """

    def __init__(self):
        self.maximum_health = 3
        self.maximum_energy = 100
        self.knockback_distance = 1
        self.cooldown = 4
        self.throw_distance = 2
        self.leap_distance = 2

    def __repr__(self):
        return str(self.__dict__)


class Status:
    """Logical representation of the player status.

    Attributes
    ----------
    cooldown : int
        Number of turns to wait before using bash again.
    energy : int
        Left energy.
    spear : bool
        `True` iff. the player has its spear in the inventory.
    health : int
        Number of full hearts.
    prayers : List[Prayer]
        List of prayers made by the player so far.
    attributes : PlayerAttributes
        Current abilities of the player.

    """

    def __init__(self):
        self.cooldown = 0
        self.energy = 100
        self.spear = True
        self.health = 3
        self.prayers = list()
        self.attributes = PlayerAttributes()

    def __repr__(self):
        return "Status%s" % self.__dict__

    def can_leap(self):
        """Check if the player can leap.

        Returns
        -------
        bool
            `True` if the player can perform a leap.

        """
        return self.energy >= 50

    def can_bash(self):
        """Check if the player can bash.

        Returns
        -------
        bool
            `True` if the player can perform a bash.

        """
        return self.cooldown == 0

    def can_throw(self):
        """Check if the player can throw its spear.

        Returns
        -------
        bool
            `True` if the player can perform a throw.

        """
        return self.spear

    def restore_energy(self, amount):
        """Restore an amount of energy.

        Parameters
        ----------
        amount : int
            Amount of energy to restore.

        """
        self.energy = min(self.energy + amount, self.attributes.maximum_energy)

    def use_energy(self, amount=50):
        """Consume an amount of energy.

        Parameters
        ----------
        amount : int
            Amount of energy to remove.

        """
        assert amount >= self.energy
        self.energy -= amount

    def restore_health(self, amount=1):
        """Heal the player.

        Parameters
        ----------
        amount : int
            Number of hearts to restore.

        """
        self.health = min(self.health + amount, self.attributes.maximum_health)

    def deal_damage(self, amount=1):
        """Damage the player.

        Parameters
        ----------
        amount : int
            Number of hearts to remove.

        Returns
        -------
        bool
            `True` if the player is still alive after taking the damages.

        """
        self.health = max(0, self.health - amount)
        if self.health == 0:
            # raise LostGameException()
            return False
        return True
