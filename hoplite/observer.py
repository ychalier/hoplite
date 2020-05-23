"""Parse game screenshots.
"""

import os
import time
import logging
import numpy
import matplotlib.image as mpimg
import hoplite.utils
import hoplite.game.terrain
import hoplite.game.state


def is_close(tgt, ref):
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
    return numpy.isclose(tgt - ref, 0, atol=.001).all()


def classify_terrain(part):  # pylint: disable=R0911, R0912
    """Classify a terrain tile.

    Parameters
    ----------
    part : numpy.ndarray
        Extracted tile image of shape (52, 52, 3).

    Returns
    -------
    hoplite.game.terrain.SurfaceElement
        Classification of the given tile.

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
        if is_spear(part):
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
        return hoplite.game.terrain.SurfaceElement.ALTAR_OFF
    if is_close(part[26, 26], [0.709804, 0.572549, 0.000000]):
        return hoplite.game.terrain.SurfaceElement.FLEECE
    if is_close(part[26, 26], [0.937255, 0.780392, 0.000000]):
        return hoplite.game.terrain.SurfaceElement.FLEECE
    if is_close(part[37, 26], [0.062745, 0.556863, 0.580392]):
        return hoplite.game.terrain.SurfaceElement.PORTAL
    if is_close(part[20, 23], [1.000000, 0.764706, 0.258824]):
        return hoplite.game.terrain.SurfaceElement.BOMB
    return None


def classify_font(part):  # pylint: disable=R0911
    """Font classifier.

    Parameters
    ----------
    part : numpy.ndarray
        Extracted image of shape (28, 20, 3).

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


def classify_hearts(part):
    """Classify player's heart.

    Parameters
    ----------
    part : numpy.ndarray
        Extracted image of shape (80, 80, 3).

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


def classify_spear(part):
    """Check if the player has a spear in inventory.

    Parameters
    ----------
    part : numpy.ndarray
        Extracted image of shape (96, 16, 3).

    Returns
    -------
    bool
        Whether the player has its spear in the inventory.

    """
    if is_close(part[40, 10], [0.937255, 0.541176, 0.192157]):
        return True
    return False


def classify_energy(part):
    """Count the number of digits in the energy number.

    Parameters
    ----------
    part : numpy.ndarray
        Extracted image of shape (28, 40, 3).

    Returns
    -------
    int
        Energy locator index.

    """
    if is_close(part[0, 0], [0.905882, 0.905882, 0.352941]):
        return 0
    if is_close(part[0, 39], [0.905882, 0.905882, 0.352941]):
        return 2
    return 1


def image_distance(reference, target):
    """l2 norm between two arrays.

    Parameters
    ----------
    reference : numpy.ndarray
        Template image.
    target : numpy.ndarray
        Image to classify.

    Returns
    -------
    float
        l2 norm between the two arrays.

    """
    return numpy.linalg.norm(target - reference)


def is_spear(array):
    """Spear detector.

    Parameters
    ----------
    array : numpy.ndarray
        Image of a tile with shape (52, 52, 3).

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


class ImagePreprocessor:  # pylint: disable=R0903
    """Image preprocessor interface.
    """

    def __init__(self):
        pass

    def apply(self, array):
        """Apply the preprocessing to an array.

        Parameters
        ----------
        array : numpy.ndarray
            Image array to preprocess.

        Returns
        -------
        numpy.ndarray
            Modified array.

        """
        raise NotImplementedError


class Thresholder(ImagePreprocessor):  # pylint: disable=R0903
    """Apply a threshold to an image.
    """

    def __init__(self, threshold):
        self.threshold = threshold
        super(Thresholder, self).__init__()

    def apply(self, array):
        for i in range(array.shape[0]):
            for j in range(array.shape[1]):
                value = 0.
                if sum(array[i, j, :3]) > 3 * self.threshold:
                    value = 1.
                for k in range(3):
                    array[i, j, k] = value
        return array


class Locator:  # pylint: disable=R0903
    """Target specific locations within an image array.

    Parameters
    ----------
    shape : tuple[int, int]
        Shape of arrays to extract.
    anchor : tuple[int, int]
        Array coordinates used as reference for the localisation.
    hmargin : int
        Horizontal margin between parts, in pixels.
    vmargin : int
        Vertical margin between parts, in pixels.
    save_parts : bool
        Whether to save extracted parts to disk.

    """

    def __init__(self, shape, anchor, hmargin=0, vmargin=0, save_parts=False):  # pylint: disable=R0913
        self.width = shape[0]
        self.height = shape[1]
        self.anchor_x = anchor[0]
        self.anchor_y = anchor[1]
        self.hmargin = hmargin
        self.vmargin = vmargin
        self.save_parts = save_parts

    def _save_part(self, part):
        if not self.save_parts:
            return
        if not os.path.isdir("parts"):
            os.mkdir("parts")
        filename = os.path.join(
            "parts",
            str(len(next(os.walk("parts"))[2])).zfill(4)
            + "-"
            + self.__class__.__name__
            + "-"
            + str(time.time()).replace(".", "").ljust(17, "0")
            + ".png"
        )
        mpimg.imsave(filename, part)

    def _extract(self, array, element_x, element_y):
        part = array[
            element_y:element_y + self.height,
            element_x:element_x + self.width,
            :3
        ]
        self._save_part(part)
        return part

    def _locate(self, i, j):
        raise NotImplementedError

    def get(self, array, i, j):
        """Locate and extract a part of an image array.

        Parameters
        ----------
        array : numpy.ndarray
            Array to extract parts from.
        i : int
            ith-row to extract.
        j : int
            jth-row to extract.

        Returns
        -------
        numpy.ndarray
            Extracted part.

        """
        element_x, element_y = self._locate(i, j)
        return self._extract(array, element_x, element_y)


class TopLeftLocator(Locator):  # pylint: disable=R0903
    """
    Locator where the `anchor` is the top-left corner of the first element.
    Elements are aligned in a grid with same-sized cells spaced by given
    margins.
    `i` refers to the rows and `j` to the columns in this grid arragement,
    0 refering to the `anchor`.
    """

    def _locate(self, i, j):
        return (
            self.anchor_x + (self.width + self.hmargin) * j,
            self.anchor_y + (self.height + self.vmargin) * i
        )


class TerrainLocator(Locator):  # pylint: disable=R0903
    """
    Locator for the hexagonal tiles of the terrain.
    `i` refers to the `y` axis and `j` to the `x` axis of the
    `hoplite.utils.HexagonalCoordinates`.
    """

    def _locate(self, i, j):
        column = j
        row = i + .5 * j
        return (
            int(self.anchor_x + self.hmargin * column - .5 * self.width),
            int(self.anchor_y - self.vmargin * row - .5 * self.height),
        )


class Observer:
    """Wrapper for screenshot parsing tools.

    Parameters
    ----------
    save_parts : bool
        Whether to save extracted parts to disk.

    Attributes
    ----------
    logger : logging.Logger
        Logger to write debug information.
    LOGGER_NAME : str
        Name of the logger.
    locators : dict[str, Locator]
        Locators that will be used for the observation.
    classifiers : dict[str, TemplateClassifier]
        Classifiers that will be used for the observation.

    """

    LOGGER_NAME = "observer"

    def __init__(self, save_parts=False):
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.locators = {
            "terrain": TerrainLocator((52, 52), (540, 903), 104, 112, save_parts=save_parts),
            "cooldown": TopLeftLocator((20, 28), (158, 1885), save_parts=save_parts),
            "depth": TopLeftLocator((20, 28), (178, 70), 4, save_parts=save_parts),
            "spear": TopLeftLocator((16, 96), (892, 1776), save_parts=save_parts),
            "hearts": TopLeftLocator((80, 80), (26, 1664), save_parts=save_parts),
            "energy_one": TopLeftLocator((20, 28), (520, 1885), 4, save_parts=save_parts),
            "energy_two": TopLeftLocator((20, 28), (508, 1885), 4, save_parts=save_parts),
            "energy_three": TopLeftLocator((20, 28), (496, 1885), 4, save_parts=save_parts),
            "energy": TopLeftLocator((40, 28), (544, 1885), save_parts=save_parts),
        }

    def _observe_integer(self, array, locator):
        buffer = ""
        column = 0
        thresholder = Thresholder(.5)
        while True:
            part = thresholder.apply(self.locators[locator].get(array, 0, column))
            label = classify_font(part)
            if label not in "0123456789":
                if buffer == "":
                    return 0
                return int(buffer)
            buffer += label
            column += 1

    def _observe_depth(self, array):
        time_start = time.time()
        depth = self._observe_integer(array, "depth")
        self.logger.debug("Observed depth in %.1f ms", 1000 * (time.time() - time_start))
        return depth

    def _observe_cooldown(self, array):
        time_start = time.time()
        cooldown = self._observe_integer(array, "cooldown")
        self.logger.debug("Observed cooldown in %.1f ms", 1000 * (time.time() - time_start))
        return cooldown

    def _observe_energy(self, array):
        time_start = time.time()
        locators = ["energy_one", "energy_two", "energy_three"]
        locator_index = classify_energy(self.locators["energy"].get(array, 0, 0))
        energy = self._observe_integer(array, locators[locator_index])
        self.logger.debug("Observed energy in %.1f ms", 1000 * (time.time() - time_start))
        return energy

    def _observe_hearts(self, array):
        time_start = time.time()
        life = [0, 0]
        column = 0
        while True:
            part = self.locators["hearts"].get(array, 0, column)
            label = classify_hearts(part)
            if label == "empty":
                break
            if label == "healthy":
                life[0] += 1
            life[1] += 1
            column += 1
        self.logger.debug("Observed hearts in %.1f ms", 1000 * (time.time() - time_start))
        return tuple(life)

    def _observe_spear(self, array):
        time_start = time.time()
        spear = classify_spear(self.locators["spear"].get(array, 0, 0))
        self.logger.debug("Observed spear in %.1f ms", 1000 * (time.time() - time_start))
        return spear

    def _observe_terrain(self, array):
        time_start = time.time()
        surface = list()
        for pos in hoplite.utils.SURFACE_COORDINATES:
            part = self.locators["terrain"].get(array, pos.y, pos.x)
            label = classify_terrain(part)
            surface.append(label)
        terrain = hoplite.game.terrain.Terrain.from_list(surface)
        self.logger.debug("Observed terrain in %.1f ms", 1000 * (time.time() - time_start))
        return terrain

    def observe(self, array):
        """Parse a screenshot.

        Parameters
        ----------
        array : numpy.ndarray
            Screenshot of shape (1920, 1080, 4).

        Returns
        -------
        hoplite.game.state.GameState
            Parsed game state.

        """
        time_start = time.time()
        state = hoplite.game.state.GameState()
        state.depth = self._observe_depth(array)
        state.terrain = self._observe_terrain(array)
        state.status.energy = self._observe_energy(array)
        state.status.cooldown = self._observe_cooldown(array)
        current_health, max_health = self._observe_hearts(array)
        state.status.health = current_health
        state.status.attributes.maximum_health = max_health
        state.status.spear = self._observe_spear(array)
        self.logger.info(
            "Observed screenshot in %.3f seconds",
            time.time() - time_start
        )
        return state

    def observe_stream(self, path):
        """Read a screenshot from a stream or a file.
        """
        return self.observe(mpimg.imread(path))

    @staticmethod
    def wait(monkey, delay, threshold=200):
        """Waits for the next playable position.

        Parameters
        ----------
        monkey : hoplite.monkey_runner.MonkeyRunnerInterface
            MonkeyRunner client.
        delay : float
            Delay in seconds between screenshots.
        threshold : int
            l2-norm threshold under which two screenshots are considered equal.

        """
        last = mpimg.imread(monkey.snapshot(as_stream=True))
        while True:
            time.sleep(delay)
            new = mpimg.imread(monkey.snapshot(as_stream=True))
            if image_distance(last, new) <= threshold:
                return
            last = new
