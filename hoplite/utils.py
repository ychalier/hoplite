"""General utilities. Mostly hexagonal coordinates tools.
"""


class HexagonalCoordinates:
    """Wrapper for hexagonal coordinates. It follows the description of this
    article:
    [*Hexagonal Grids*, by Red Blob Games](https://www.redblobgames.com/grids/hexagons/).
    Here is a plot of what it looks like: ![](https://i.imgur.com/EOaG67E.png)

    Attributes
    ----------
    x : float
        Horizontal axis.
    y : float
        Diagonal axis pointing toward the northwest corner.
    z : float
        Diagonal axis pointing toward the southwest corner.

    """

    def __init__(self, x, y):
        # pylint: disable=C0103
        self.x = x
        self.y = y
        self.z = - x - y

    def __repr__(self):
        return str((self.x, self.y))

    def __str__(self):
        return str((self.x, self.y, self.z))

    def __iter__(self):
        return iter([self.x, self.y])

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if other is None:
            return False
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return HexagonalCoordinates(
            self.x + other.x,
            self.y + other.y
        )

    def __sub__(self, other):
        return HexagonalCoordinates(
            self.x - other.x,
            self.y - other.y
        )

    def __mul__(self, value):
        return HexagonalCoordinates(
            self.x * value,
            self.y * value
        )

    def __truediv__(self, value):
        return HexagonalCoordinates(
            self.x / value,
            self.y / value
        )

    def __floordiv__(self, value):
        return HexagonalCoordinates(
            self.x // value,
            self.y // value
        )

    def norm(self):
        """Compute the infinite norm of the vector.

        Returns
        -------
        float
            Infinite norm of the position considered as a vector.

        """
        return max(abs(self.x), abs(self.y), abs(self.z))

    def gradient(self, other):
        """Compute the direction between two positions.

        Parameters
        ----------
        other : HexagonalCoordinates
            Destination position.

        Returns
        -------
        HexagonalCoordinates
            Gradient vector of the displacement from `self` to `other`.

        """
        gap = other - self
        return gap / gap.norm()

    def doubled(self):
        """Doubled coordinates of the position.

        Returns
        -------
        tuple[float, float]
            Doubled coordinates equivalent of the position.

        """
        return (self.x, self.y + .5 * self.x)

    def copy(self):
        """Copy itself.

        Returns
        -------
        HexagonalCoordinates
            Same position but different address.

        """
        return HexagonalCoordinates(self.x, self.y)

    def rotate(self, steps):
        """Rotate an hexagonal vector.

        Parameters
        ----------
        steps : int
            Number of rotation steps. One step corresponds to a angle of pi/3,
            i.e. one sixth of a circle, in trigonometric direction
            (counterclockwise). A negative number of steps will rotate
            clockwise.

        Returns
        -------
        HexagonalCoordinates
            Rotated vector.

        """
        clockwise = steps < 0
        result = self.copy()
        for _ in range(abs(steps)):
            if clockwise:
                result = HexagonalCoordinates(-result.z, -result.x)
            else:
                result = HexagonalCoordinates(-result.y, -result.z)
        return result


def iter_coords():
    """Iterates over the coordinates of the map.

    Returns
    -------
    Iterator[HexagonalCoordinates]
        Iterator over the 79 tiles of the map.

    """
    # pylint: disable=C0103
    for x, height in zip(range(-4, 5), [7, 8, 9, 10, 11, 10, 9, 8, 7]):
        if x >= 0:
            start = -5
        else:
            start = - 5 - x
        for y in range(start, start + height):
            yield HexagonalCoordinates(x, y)


SURFACE_COORDINATES = list(iter_coords())
HEXAGONAL_DIRECTIONS = [
    HexagonalCoordinates(1, 0),
    HexagonalCoordinates(-1, 0),
    HexagonalCoordinates(0, 1),
    HexagonalCoordinates(0, -1),
    HexagonalCoordinates(-1, 1),
    HexagonalCoordinates(1, -1),
]


def hexagonal_neighbors(pos):
    """Return the set of surrounding positions in an hexagonal grid.

    Parameters
    ----------
    pos : HexagonalCoordinates
        Center position.

    Returns
    -------
    set[HexagonalCoordinates]
        Set of positions surrounding the center.

    """
    return set(pos + direction for direction in HEXAGONAL_DIRECTIONS)\
        .intersection(SURFACE_COORDINATES)


def hexagonal_circle(center, radius):
    """Compute an hexagonal circle given a center and a radius.

    Parameters
    ----------
    center : HexagonalCoordinates
        Center of the hexagonal circle.
    radius : int
        Radius of the hexagonal circle (using the infinite norm
        of `HexagonalCoordinates.norm`).

    Returns
    -------
    set[HexagonalCoordinates]
        Set of positions within the hexagonal circle of given center and radius.

    """
    return {
        pos for pos in SURFACE_COORDINATES
        if (pos - center).norm() <= radius
    }


def hexagonal_line(start, direction):
    """Compute an hexagonal line given a starting position and a direction.

    Parameters
    ----------
    start : HexagonalCoordinates
        Beginning of the line.
    direction : HexagonalCoordinates
        Direction (vector of norm 1) of the line.

    Returns
    -------
    list[HexagonalCoordinates]
        Tiles within the hexagonal line, from `start` and going.

    """
    result = [start]
    while True:
        current = result[-1] + direction
        if current not in SURFACE_COORDINATES:
            break
        result.append(current)
    return result
