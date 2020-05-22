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
        Image of a tile with shape (52, 52, 4).

    Returns
    -------
    bool
        Whether the tile contains a spear.

    """
    reference = numpy.array([
        [.9372549, .5411765, .19215687, 1.],
        [.4509804, .27058825, .09411765, 1.]
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


class TemplateClassifier:
    """Compute the best matching template for a fixed-size input image.

    Parameters
    ----------
    shape : tuple[int, int]
        Template image shape.
    labels : dict[A, list[str]]
        Possible output labels, with their associated image file paths.
    preprocessors : list[ImagePreprocessor]
        Preprocessing steps to apply to images before classifying them.

    Attributes
    ----------
    width : int
        Template image width.
    height : int
        Template image height.
    registry : dict[A, list[numpy.ndarray]]
        Possible output labels, with their associated images.
    labels
    preprocessors

    """

    def __init__(self, shape, labels, preprocessors=None):
        self.width = shape[0]
        self.height = shape[1]
        self.labels = labels
        if preprocessors is None:
            self.preprocessors = list()
        else:
            self.preprocessors = preprocessors
        self.registry = dict()

    def build(self):
        """Load template image files.
        """
        self.registry = {
            label: [
                mpimg.imread(template)
                for template in templates
            ]
            for label, templates in self.labels.items()
        }


    def _preprocess(self, array):
        preprocessed = numpy.copy(array)
        for preprocessor in self.preprocessors:
            preprocessed = preprocessor.apply(preprocessed)
        return preprocessed

    def _classify(self, array):
        distances = {
            label: self._test(array, label)
            for label in self.registry
        }
        return min(distances.items(), key=lambda x: x[1])

    def _test(self, array, label):
        distance = float("inf")
        for template in self.registry[label]:
            distance = min(
                distance,
                image_distance(self._preprocess(array), template)
            )
        return distance

    def test(self, array, label):
        """Test a label.

        Parameters
        ----------
        array : numpy.ndarray
            Image to classify.
        label : A
            Candidate label.

        Returns
        -------
        float
            Minimum l2 norm between the preprocessed input `array` and the
            templates associated to the input `label`.

        """
        return self._test(self._preprocess(array), label)

    def classify(self, array):
        """Classify an image array.

        Parameters
        ----------
        array : numpy.ndarray
            Image to classify.

        Returns
        -------
        A
            Best matching label.

        """
        return self._classify(self._preprocess(array))[0]


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
            :
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
            "energy_three": TopLeftLocator((20, 28), (496, 1885), 4, save_parts=save_parts)
        }
        self.classifiers = {
            "terrain": TemplateClassifier(
                (52, 52),
                {
                    hoplite.game.terrain.SurfaceElement.GROUND:
                        ["templates/terrain/ground.png"],
                    hoplite.game.terrain.SurfaceElement.MAGMA:
                        ["templates/terrain/magma.png"],
                    hoplite.game.terrain.SurfaceElement.STAIRS:
                        ["templates/terrain/stairs.png"],
                    hoplite.game.terrain.SurfaceElement.ALTAR_ON:
                        ["templates/terrain/altar_on.png",
                         "templates/terrain/altar_on2.png"],
                    hoplite.game.terrain.SurfaceElement.ALTAR_OFF:
                        ["templates/terrain/altar_off.png"],
                    hoplite.game.terrain.SurfaceElement.PLAYER:
                        ["templates/terrain/player.png"],
                    hoplite.game.terrain.SurfaceElement.ARCHER:
                        ["templates/terrain/archer.png"],
                    hoplite.game.terrain.SurfaceElement.FOOTMAN:
                        ["templates/terrain/footman.png"],
                    hoplite.game.terrain.SurfaceElement.DEMOLITIONIST_WITHOUT_BOMB:
                        ["templates/terrain/demolitionist_no_bomb.png"],
                    hoplite.game.terrain.SurfaceElement.DEMOLITIONIST_HOLDING_BOMB:
                        ["templates/terrain/demolitionist_bomb.png"],
                    hoplite.game.terrain.SurfaceElement.WIZARD_CHARGED:
                        ["templates/terrain/wizard_charged.png"],
                    hoplite.game.terrain.SurfaceElement.WIZARD_DISCHARGED:
                        ["templates/terrain/wizard_discharged.png"],
                    hoplite.game.terrain.SurfaceElement.BOMB:
                        ["templates/terrain/bomb.png"],
                    hoplite.game.terrain.SurfaceElement.FLEECE:
                        ["templates/terrain/fleece.png"],
                    hoplite.game.terrain.SurfaceElement.PORTAL:
                        ["templates/terrain/portal.png"],
                }
            ),
            "font": TemplateClassifier(
                (20, 28),
                {
                    "0": ["templates/font/0.png"],
                    "1": ["templates/font/1.png"],
                    "2": ["templates/font/2.png"],
                    "3": ["templates/font/3.png"],
                    "4": ["templates/font/4.png"],
                    "5": ["templates/font/5.png"],
                    "6": ["templates/font/6.png"],
                    "7": ["templates/font/7.png"],
                    "8": ["templates/font/8.png"],
                    "9": ["templates/font/9.png"],
                    "empty": ["templates/font/empty.png"],
                    "lightning": ["templates/font/lightning.png"],
                },
                [Thresholder(.5)]
            ),
            "hearts": TemplateClassifier((80, 80), {
                "empty": ["templates/hearts/empty.png"],
                "healthy": ["templates/hearts/healthy.png"],
                "hurt": ["templates/hearts/hurt.png"]
            }),
            "spear": TemplateClassifier((16, 96), {
                "on": ["templates/spear/on.png"],
                "off": ["templates/spear/off.png"]
            })
        }

    def build(self):
        """Prepare all classifiers.
        """
        time_start = time.time()
        for name, classifier in self.classifiers.items():
            self.logger.debug("Building %s classifier", name)
            classifier.build()
        self.logger.info(
            "Built classifiers in %f seconds",
            time.time() - time_start
        )

    def _observe_integer(self, array, locator):
        buffer = ""
        column = 0
        while True:
            part = self.locators[locator].get(array, 0, column)
            label = self.classifiers["font"].classify(part)
            if label not in "0123456789":
                if buffer == "":
                    return 0
                return int(buffer)
            buffer += label
            column += 1

    def _observe_depth(self, array):
        self.logger.debug("Observing depth")
        return self._observe_integer(array, "depth")

    def _observe_cooldown(self, array):
        self.logger.debug("Observing cooldown")
        return self._observe_integer(array, "cooldown")

    def _observe_energy(self, array):
        self.logger.debug("Observing energy")
        distances = {
            locator: self.classifiers["font"].test(
                self.locators[locator].get(array, 0, i + 1),
                "lightning"
            )
            for i, locator in enumerate([
                "energy_one",
                "energy_two",
                "energy_three"
            ])
        }
        return self._observe_integer(
            array,
            min(distances.items(), key=lambda x: x[1])[0]
        )

    def _observe_hearts(self, array):
        self.logger.debug("Observing hearts")
        life = [0, 0]
        column = 0
        while True:
            part = self.locators["hearts"].get(array, 0, column)
            label = self.classifiers["hearts"].classify(part)
            if label == "empty":
                return tuple(life)
            if label == "healthy":
                life[0] += 1
            life[1] += 1
            column += 1
        return tuple(life)

    def _observe_spear(self, array):
        self.logger.debug("Observing spear")
        return self.classifiers["spear"].classify(self.locators["spear"].get(array, 0, 0)) == "on"

    def _observe_terrain(self, array):
        self.logger.debug("Observing terrain")
        surface = list()
        for pos in hoplite.utils.SURFACE_COORDINATES:
            part = self.locators["terrain"].get(array, pos.y, pos.x)
            label = self.classifiers["terrain"].classify(part)
            if label == hoplite.game.terrain.SurfaceElement.GROUND and is_spear(part):
                surface.append(hoplite.game.terrain.SurfaceElement.SPEAR)
            else:
                surface.append(label)
        return hoplite.game.terrain.Terrain.from_list(surface)

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
            "Observed screenshot in %f seconds",
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
