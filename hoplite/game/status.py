"""Representation of the abstract status of the player.
"""

import enum


@enum.unique
class Prayer(enum.Enum):
    """
    Prayers obtained at the altars.
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
    spree : int
        Current killing spree counter.
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
        self.spree = 0
        self.prayers = list()
        self.attributes = PlayerAttributes()

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __repr__(self):
        text = "/".join([
            str(self.cooldown),
            str(self.energy),
            str(int(self.spear)),
            str(self.health),
            str(self.spree),
            ",".join([str(prayer.value) for prayer in self.prayers])
        ])
        if text[-1] == "/":
            return text + "-"
        return text

    def __str__(self):
        return "Status%s" % self.__dict__

    @classmethod
    def from_string(cls, string):
        """Create and return a `Status` object from its string representation.

        Parameters
        ----------
        string : str
            String representation of the status. A string of 6 values separated
            by a slash. First five values are integers, the last one is a list
            of comma-separated integers, corresponding to the prayers indices.

        Returns
        -------
        Status
            Status corresponding to this string.

        """
        status = cls()
        cooldown, energy, spear, health, spree, prayers = string.split("/")
        status.cooldown = int(cooldown)
        status.energy = int(energy)
        status.spear = spear == "1"
        status.health = int(health)
        status.spree = int(spree)
        for prayer in prayers.split(","):
            if prayer != "-":
                status.add_prayer(Prayer(int(prayer)), False)
        return status

    def add_prayer(self, prayer, online=True):  # pylint: disable=R0912
        """Add a prayer to the prayer list.

        Parameters
        ----------
        prayer : hoplite.game.status.Prayer
            Prayer to add to the list.
        online : bool
            If `True`, then changes on health an energy will also affects the
            live values, i.e. restoring health or energy. This is not wanted
            when artificially adding prayers to a game state already parsed
            from a screenshot (where health and energy values) already take
            prayers effects into account.

        """
        self.prayers.append(prayer)
        if prayer == Prayer.DIVINE_RESTORATION and online:
            self.health = self.attributes.maximum_health
        elif prayer == Prayer.FORTITUDE:
            if online:
                self.health += 1
            self.attributes.maximum_health += 1
        elif prayer == Prayer.BLOODLUST:
            if online:
                self.health -= 1
            self.attributes.maximum_health -= 1
        elif prayer == Prayer.MIGHTY_BASH:
            self.attributes.knockback_distance += 1
        elif prayer == Prayer.QUICK_BASH:
            self.attributes.cooldown -= 1
        elif prayer == Prayer.GREATER_THROW:
            self.attributes.throw_distance += 1
        elif prayer == Prayer.GREATER_THROW_II:
            self.attributes.throw_distance += 1
            if online:
                self.health -= 1
            self.attributes.maximum_health -= 1
        elif prayer == Prayer.GREATER_ENERGY:
            self.attributes.maximum_energy += 20
            if online:
                self.energy += 20
        elif prayer == Prayer.GREATER_ENERGY_II:
            self.attributes.maximum_energy += 15
            if online:
                self.energy += 15
                self.health -= 1
            self.attributes.maximum_health -= 1
        elif prayer == Prayer.WINGED_SANDALS:
            self.attributes.leap_distance += 1
            if online:
                self.health -= 1
            self.attributes.maximum_health -= 1
        elif prayer == Prayer.SURGE:
            if online:
                self.health -= 1
            self.attributes.maximum_health -= 1
        elif prayer == Prayer.REGENERATION:
            if online:
                self.health -= 1
            self.attributes.maximum_health -= 1
        elif prayer == Prayer.STAGGERING_LEAP:
            if online:
                self.health -= 2
            self.attributes.maximum_health -= 2


    def update(self, new_status):
        """Update the current status with a newly parsed one.

        Parameters
        ----------
        new_status : Status
            New status, recently parsed.

        """
        self.cooldown = new_status.cooldown
        self.energy = new_status.energy
        self.spear = new_status.spear
        self.health = new_status.health
        self.spree = new_status.spree
        for prayer in new_status.prayers:
            self.add_prayer(prayer, False)
        # Attributes are automatically computed when adding the prayer

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

    def restore_energy(self, amount=10):
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
        assert amount <= self.energy, (amount, self.energy)
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
