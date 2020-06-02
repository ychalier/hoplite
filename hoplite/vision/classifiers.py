# pylint: disable=R0911, R0912
"""Classifiers for recognizing templates on parts of screen.
"""

import numpy
import hoplite.game.terrain
import hoplite.game.status


def is_close(tgt, ref, tol=.001):
    """Check if two pixels are of same color.

    Parameters
    ----------
    tgt : numpy.ndarray
        Target pixel (vector).
    ref : numpy.ndarray
        Rerence pixel (vector).

    Returns
    -------
    bool
        `True` if pixels are the same.

    """
    return numpy.isclose(tgt - ref, 0, atol=tol).all()


def terrain(part):
    """Classify a terrain tile.

    Parameters
    ----------
    part : numpy.ndarray
        Tile image array of shape `(52, 52, 3)`.

    Returns
    -------
    hoplite.game.terrain.SurfaceElement
        `hoplite.game.terrain.SurfaceElement` representation for that tile.

    """
    if is_close(part[10, 0], [0.290196, 0.301961, 0.290196])\
            or is_close(part[10, 0], [0.223529, 0.235294, 0.223529]):
        if is_close(part[45, 40], [0.937255, 0.541176, 0.192157]):
            return hoplite.game.terrain.SurfaceElement.FOOTMAN
        if is_close(part[15, 26], [0.611765, 0.890196, 0.352941]):
            return hoplite.game.terrain.SurfaceElement.ARCHER
        if is_close(part[37, 37], [0.741176, 0.141176, 0.192157]):
            return hoplite.game.terrain.SurfaceElement.PLAYER
        if is_close(part[20, 23], [1.000000, 0.764706, 0.258824]):
            return hoplite.game.terrain.SurfaceElement.BOMB
        if is_close(part[26, 26], [0.4509804, 0.27058825, 0.09411765]):
            return hoplite.game.terrain.SurfaceElement.SPEAR
        if is_close(part[26, 26], [0.9372549, 0.5411765, 0.19215687]):
            return hoplite.game.terrain.SurfaceElement.SPEAR
        return hoplite.game.terrain.SurfaceElement.GROUND
    if is_close(part[15, 15], numpy.array([0.41960785, 0.07843138, 0.0627451])):
        return hoplite.game.terrain.SurfaceElement.MAGMA
    if is_close(part[33, 28], [0.905882, 0.364706, 0.352941]):
        return hoplite.game.terrain.SurfaceElement.DEMOLITIONIST_HOLDING_BOMB
    if is_close(part[33, 28], [0.160784, 0.254902, 0.258824]):
        return hoplite.game.terrain.SurfaceElement.DEMOLITIONIST_WITHOUT_BOMB
    if is_close(part[48, 26], [0.741176, 0.286275, 0.517647]):
        if is_close(part[0, 0], [0.741176, 0.141176, 0.192157]):
            return hoplite.game.terrain.SurfaceElement.WIZARD_CHARGED
        return hoplite.game.terrain.SurfaceElement.WIZARD_DISCHARGED
    if is_close(part[37, 37], [0.741176, 0.141176, 0.192157]):
        return hoplite.game.terrain.SurfaceElement.PLAYER
    if is_close(part[15, 15], [0.321569, 0.427451, 0.223529]):
        return hoplite.game.terrain.SurfaceElement.STAIRS
    if is_close(part[42, 51], [0.905882, 0.364706, 0.352941]):
        return hoplite.game.terrain.SurfaceElement.ALTAR_ON
    if is_close(part[0, 0], numpy.array([0.321569, 0.427451, 0.223529])):
        if is_close(part[28, 0], [0.129412, 0.141176, 0.129412]):
            return hoplite.game.terrain.SurfaceElement.ALTAR_ON
        return hoplite.game.terrain.SurfaceElement.ALTAR_OFF
    if part[26, 26, 2] == 0 and\
        abs(part[26, 26, 0] * 0.80465513 + 0.018641233 - part[26, 26, 1]) < .03:
        return hoplite.game.terrain.SurfaceElement.FLEECE
    if is_close(part[37, 26], [0.062745, 0.556863, 0.580392]):
        return hoplite.game.terrain.SurfaceElement.PORTAL
    if is_close(part[37, 26], [0.6117647, 0.68235296, 0.8392157]):
        return hoplite.game.terrain.SurfaceElement.PORTAL
    if is_close(part[20, 23], [1.000000, 0.764706, 0.258824]):
        return hoplite.game.terrain.SurfaceElement.BOMB
    if is_close(part[26, 26], [0.4509804, 0.27058825, 0.09411765]):
        return hoplite.game.terrain.SurfaceElement.SPEAR
    if is_close(part[26, 26], [0.9372549, 0.5411765, 0.19215687]):
        return hoplite.game.terrain.SurfaceElement.SPEAR
    return None


def font(part):
    """Font classifier. Supports digits from 0 to 9, lightning symbol, and
    space.

    Parameters
    ----------
    part : numpy.ndarray
        Character image array of shape `(28, 20, 3)`.

    Returns
    -------
    str
        Recognized character.

    """
    if is_close(part[0, 9], [1., 1., 1.]):
        if is_close(part[0, 5], [1., 1., 1.]):
            if is_close(part[0, 0], [1., 1., 1.]):
                if is_close(part[20, 10], [1., 1., 1.]):
                    if is_close(part[0, 17], [0., 0., 0.]):
                        return "lightning"
                    return "7"
                return "5"
            if is_close(part[20, 2], [1., 1., 1.]):
                if is_close(part[17, 17], [0., 0., 0.]):
                    return "2"
                if is_close(part[10, 0], [1., 1., 1.]):
                    if is_close(part[12, 0], [0., 0., 0.]):
                        return "8"
                    return "0"
                return "3"
            return "9"
        if is_close(part[10, 0], [1., 1., 1.]):
            return "6"
        return "1"
    if is_close(part[9, 5], [1., 1., 1.]):
        return "4"
    return "empty"


def hearts(part):
    """Classify a lifebar heart.

    Parameters
    ----------
    part : numpy.ndarray
        Heart image array of shape `(80, 80, 3)`.

    Returns
    -------
    str
        Either `"healthy"`, `"hurt"` or `"empty"`.

    """
    if is_close(part[50, 40], [0.741176, 0.141176, 0.192157]):
        return "healthy"
    if is_close(part[50, 40], [0.321569, 0.333333, 0.321569]):
        return "hurt"
    return "empty"


def spear(part):
    """Check if the player has a spear in inventory.

    Parameters
    ----------
    part : numpy.ndarray
        Spear image array of shape `(96, 16, 3)`.

    Returns
    -------
    bool
        Whether the player has its spear in the inventory.

    """
    return is_close(part[40, 10], [0.937255, 0.541176, 0.192157])


def energy(part):
    """Count the number of digits in the energy number.

    Parameters
    ----------
    part : numpy.ndarray
        Right part of an energy image array of shape `(28, 40, 3)`.

    Returns
    -------
    int
        Number of digits in the energy counter (excluding lightning).

    """
    if is_close(part[0, 0], [0.905882, 0.905882, 0.352941]):
        return 1
    if is_close(part[0, 39], [0.905882, 0.905882, 0.352941]):
        return 3
    return 2


def is_spear(array):
    """Check if a ground tile contains a spear. The difficult part is that the
    spear is rotated depending on where the player thrown it from.

    Parameters
    ----------
    array : numpy.ndarray
        Tile image array of shape `(52, 52, 3)`.

    Returns
    -------
    bool
        Whether the tile contains a spear.

    """
    reference = numpy.array([
        [.9372549, .5411765, .19215687],
        [.4509804, .27058825, .09411765]
    ])
    for index in [(25, 25), (25, 26), (26, 25), (26, 26)]:
        if numpy.all(numpy.isclose(reference - array[index], 0, .001), axis=1).any():
            return True
    return False


def interface(part):
    """Detect which of `hoplite.game.state.Interface` is displayed on screen.

    Parameters
    ----------
    part : numpy.ndarray
        Screenshot array of shape `(1920, 1080, 3)`.

    Returns
    -------
    hoplite.game.state.Interface
        Interface currently displayed on screen.

    """
    if is_close(part[600, 1000], [0.352941, 0.270588, 0.160784]):
        return hoplite.game.state.Interface.ALTAR
    if is_close(part[600, 1000], [0.290196, 0.301961, 0.290196]):
        return hoplite.game.state.Interface.ALTAR
    if is_close(part[635, 640], [0.647059, 0.000000, 0.000000]):
        return hoplite.game.state.Interface.DEATH
    if is_close(part[80, 20], [1.000000, 1.000000, 1.000000]):
        return hoplite.game.state.Interface.EMBARK
    if is_close(part[1000, 540], [0.937255, 0.764706, 0.000000]):
        return hoplite.game.state.Interface.FLEECE
    if is_close(part[275, 640], [1.000000, 1.000000, 1.000000]):
        return hoplite.game.state.Interface.VICTORY
    if is_close(part[1450, 540], [1.000000, 1.000000, 1.000000]):
        return hoplite.game.state.Interface.STAIRS
    if is_close(part[750, 1000], [0.352941, 0.270588, 0.160784]):
        return hoplite.game.state.Interface.ALTAR
    return hoplite.game.state.Interface.PLAYING


def prayer(part):
    """Classify prayers available (i.e. not grayed) at an altar.

    Parameters
    ----------
    part : numpy.ndarray
        Prayer image array of shape `(120, 900, 3)`.

    Returns
    -------
    hoplite.game.status.Prayer
        Detected prayers.

    """
    if is_close(part[75, 90], [1.000000, 0.827451, 0.000000]):
        return hoplite.game.status.Prayer.DIVINE_RESTORATION
    if is_close(part[75, 90], [0.905882, 0.364706, 0.352941]):
        return hoplite.game.status.Prayer.FORTITUDE
    if is_close(part[100, 50], [0.388235, 0.286275, 0.094118]):
        if is_close(part[50, 795], [1.000000, 1.000000, 1.000000]):
            return hoplite.game.status.Prayer.GREATER_ENERGY_II
        if is_close(part[38, 580], [1.000000, 1.000000, 1.000000]):
            if is_close(part[60, 735], [0.352941, 0.270588, 0.160784]):
                return hoplite.game.status.Prayer.WINGED_SANDALS
            return hoplite.game.status.Prayer.STAGGERING_LEAP
        return hoplite.game.status.Prayer.BLOODLUST
    if is_close(part[100, 83], [0.937255, 0.541176, 0.192157]):
        if is_close(part[50, 680], [1.000000, 1.000000, 1.000000]):
            return hoplite.game.status.Prayer.GREATER_THROW
        return hoplite.game.status.Prayer.DEEP_LUNGE
    if is_close(part[50, 50], [0.482353, 0.380392, 0.258824]):
        return hoplite.game.status.Prayer.GREATER_ENERGY
    if is_close(part[87, 72], [0.450980, 0.443137, 0.450980]):
        if is_close(part[60, 370], [0.352941, 0.270588, 0.160784]):
            return hoplite.game.status.Prayer.QUICK_BASH
        if is_close(part[60, 638], [1.000000, 1.000000, 1.000000]):
            if is_close(part[89, 215], [0.352941, 0.270588, 0.160784]):
                return hoplite.game.status.Prayer.SWEEPING_BASH
            return hoplite.game.status.Prayer.SPINNING_BASH
        return hoplite.game.status.Prayer.MIGHTY_BASH
    if is_close(part[50, 200], [1.000000, 1.000000, 1.000000]):
        if is_close(part[60, 755], [1.000000, 1.000000, 1.000000]):
            return hoplite.game.status.Prayer.GREATER_THROW_II
        return hoplite.game.status.Prayer.DEEP_LUNGE
    if is_close(part[36, 536], [1.000000, 1.000000, 1.000000]):
        return hoplite.game.status.Prayer.REGENERATION
    if is_close(part[86, 300], [1.000000, 1.000000, 1.000000]):
        return hoplite.game.status.Prayer.SURGE
    if is_close(part[70, 82], [0.968627, 0.890196, 0.419608]):
        return hoplite.game.status.Prayer.PATIENCE
    return None


def spree(part):
    """Classify a killing spree skull.

    Parameters
    ----------
    part : numpy.ndarray
        Skull image array of shape `(72, 30, 3)`.

    Returns
    -------
    str
        Either `"empty"`, `"off"` or `"on"`.

    """
    if is_close(part[36, 30], [0.094118, 0.094118, 0.094118]):
        return "empty"
    if is_close(part[36, 30], [0.321569, 0.333333, 0.321569]):
        return "off"
    # if is_close(part[36, 30], [0.482353, 0.443137, 0.192157]):
    return "on"
