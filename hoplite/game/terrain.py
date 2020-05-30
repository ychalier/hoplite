"""Representation of the terrain of the game.
"""

import math
import enum
import pygame
import hoplite.utils
import hoplite.game.demons


def draw_regular_polygon(surface, color, vertex_count, radius, position):
    """Small function to draw regular polygon on Pygame surfaces.

    Parameters
    ----------
    surface : pygame.Surface
        Surface to draw to.
    color : tuple[int, int, int, int]
        Color in RGBA format (scaling from 0 to 255).
    vertex_count : int
        Number of vertex in the polygon. 6 is hexagon.
    radius : int
        Polygon radius in pixels.
    position : tuple[int, int]
        Position, in pixels, of the polygon center.

    """
    pygame.draw.polygon(surface, color, [
        (
            position[0] + radius * math.cos(2 * math.pi * i / vertex_count),
            position[1] + radius * math.sin(2 * math.pi * i / vertex_count)
        )
        for i in range(vertex_count)
    ])


@enum.unique
class Tile(enum.Enum):
    """
    Enumeration of tiles composing the surface of the map.
    """

    GROUND = 0
    MAGMA = 1


@enum.unique
class SurfaceElement(enum.Enum):
    """
    Enumeration of the possible content of the map tiles.
    """

    GROUND = 0
    MAGMA = 1
    FOOTMAN = 2
    ARCHER = 3
    DEMOLITIONIST_HOLDING_BOMB = 4
    DEMOLITIONIST_WITHOUT_BOMB = 5
    WIZARD_CHARGED = 6
    WIZARD_DISCHARGED = 7
    SPEAR = 8
    BOMB = 9
    PLAYER = 10
    STAIRS = 11
    ALTAR_ON = 12
    ALTAR_OFF = 13
    FLEECE = 14
    PORTAL = 15


SURFACE_ELEMENT_ENCODER = {
    element: "0123456789abcdef"[element.value]
    for element in SurfaceElement
}

SURFACE_ELEMENT_DECODER = {
    "0123456789abcdef"[element.value]: element
    for element in SurfaceElement
}


class Terrain:  # pylint: disable=R0902
    """Logical representation of the game terrain.

    Attributes
    ----------
    player : hoplite.utils.HexagonalCoordinates
        Player location.
    surface : dict[hoplite.utils.HexagonalCoordinates, Tile]
        Tile composition of the surface.
    demons : dict[hoplite.utils.HexagonalCoordinates, hoplite.game.demons.Demon]
        Location of alive demons.
    bombs : set[hoplite.utils.HexagonalCoordinates]
        Location of active bombs.
    spear : hoplite.utils.HexagonalCoordinates
        Location of the spear, `None` if not present.
    altar : hoplite.utils.HexagonalCoordinates
        Location of the altar of Apollo.
    altar_prayable : bool
        Whether a prayer can be made at the altar.
    fleece : hoplite.utils.HexagonalCoordinates
        Location of the fleece, `None` if not present.
    portal : hoplite.utils.HexagonalCoordinates
        Location of the portal, `None` if not present.
    stairs : hoplite.utils.HexagonalCoordinates
        Location of the stairs.

    """

    def __init__(self):
        self.player = hoplite.utils.HexagonalCoordinates(0, -4)
        self.surface = dict()
        self.demons = dict()
        self.bombs = set()
        self.spear = None
        self.altar = None
        self.altar_prayable = False
        self.fleece = None
        self.portal = None
        self.stairs = hoplite.utils.HexagonalCoordinates(0, 4)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return repr(self) == repr(other)

    def to_list(self):  # pylint: disable=R0912
        """Represent the terrain as a list of `SurfaceElement`.

        Returns
        -------
        list[SurfaceElement]
            SurfaceElement representing the terrain map in the order of
            `SURFACE_COORDINATES`.

        """
        result = list()
        for pos in hoplite.utils.SURFACE_COORDINATES:
            if pos == self.player:
                result.append(SurfaceElement.PLAYER)
            elif pos == self.spear:
                result.append(SurfaceElement.SPEAR)
            elif pos == self.altar:
                if self.altar_prayable:
                    result.append(SurfaceElement.ALTAR_ON)
                else:
                    result.append(SurfaceElement.ALTAR_OFF)
            elif pos == self.fleece:
                result.append(SurfaceElement.FLEECE)
            elif pos == self.portal:
                result.append(SurfaceElement.PORTAL)
            elif pos in self.bombs:
                result.append(SurfaceElement.BOMB)
            elif pos == self.stairs:
                result.append(SurfaceElement.STAIRS)
            elif pos in self.demons:
                demon = self.demons[pos]
                if demon.skill == hoplite.game.demons.DemonSkill.FOOTMAN:
                    result.append(SurfaceElement.FOOTMAN)
                elif demon.skill == hoplite.game.demons.DemonSkill.ARCHER:
                    result.append(SurfaceElement.ARCHER)
                elif demon.skill == hoplite.game.demons.DemonSkill.DEMOLITIONIST:
                    if demon.holds_bomb:
                        result.append(
                            SurfaceElement.DEMOLITIONIST_HOLDING_BOMB)
                    else:
                        result.append(
                            SurfaceElement.DEMOLITIONIST_WITHOUT_BOMB)
                elif demon.skill == hoplite.game.demons.DemonSkill.WIZARD:
                    if demon.charged_wand:
                        result.append(SurfaceElement.WIZARD_CHARGED)
                    else:
                        result.append(SurfaceElement.WIZARD_DISCHARGED)
            elif pos in self.surface:
                if self.surface[pos] == Tile.GROUND:
                    result.append(SurfaceElement.GROUND)
                elif self.surface[pos] == Tile.MAGMA:
                    result.append(SurfaceElement.MAGMA)
            else:
                raise ValueError("Wrong position: %s" % pos)
        return result

    @classmethod
    def from_string(cls, string):
        """Create and return a `Terrain` object from its string representation.

        Parameters
        ----------
        string : str
            String representation of the terrain. A string of 79 characters,
            as expressed in the `SURFACE_ELEMENT_ENCODER`.

        Returns
        -------
        Terrain
            Terrain corresponding to this string.

        """
        return Terrain.from_list([SURFACE_ELEMENT_DECODER[char] for char in string])

    @classmethod
    def from_list(cls, source):  # pylint: disable=R0912
        """Create and return a `Terrain` object from a `SurfaceElement` list.

        Parameters
        ----------
        source : List[SurfaceElement]
            List of surface elements in the `SURFACE_COORDINATES` order.

        Returns
        -------
        Terrain
            Terrain corresponding to this list of elements.

        """
        terrain = cls()
        for pos, elt in zip(hoplite.utils.SURFACE_COORDINATES, source):
            terrain.surface[pos] = Tile.GROUND
            if elt == SurfaceElement.MAGMA:
                terrain.surface[pos] = Tile.MAGMA
            if elt == SurfaceElement.FOOTMAN:
                terrain.demons[pos] = hoplite.game.demons.Footman()
            elif elt == SurfaceElement.ARCHER:
                terrain.demons[pos] = hoplite.game.demons.Archer()
            elif elt == SurfaceElement.DEMOLITIONIST_HOLDING_BOMB:
                terrain.demons[pos] = hoplite.game.demons.Demolitionist(True)
            elif elt == SurfaceElement.DEMOLITIONIST_WITHOUT_BOMB:
                terrain.demons[pos] = hoplite.game.demons.Demolitionist(False)
            elif elt == SurfaceElement.WIZARD_CHARGED:
                terrain.demons[pos] = hoplite.game.demons.Wizard(True)
            elif elt == SurfaceElement.WIZARD_DISCHARGED:
                terrain.demons[pos] = hoplite.game.demons.Wizard(False)
            elif elt == SurfaceElement.SPEAR:
                terrain.spear = pos
            elif elt == SurfaceElement.BOMB:
                terrain.bombs.add(pos)
            elif elt == SurfaceElement.PLAYER:
                terrain.player = pos
            elif elt == SurfaceElement.STAIRS:
                terrain.stairs = pos
            elif elt == SurfaceElement.ALTAR_ON:
                terrain.altar = pos
                terrain.altar_prayable = True
            elif elt == SurfaceElement.ALTAR_OFF:
                terrain.altar = pos
                terrain.altar_prayable = False
            elif elt == SurfaceElement.FLEECE:
                terrain.fleece = pos
            elif elt == SurfaceElement.PORTAL:
                terrain.portal = pos
        return terrain

    def __repr__(self):
        text = ""
        for elt in self.to_list():
            text += SURFACE_ELEMENT_ENCODER[elt]
        return text

    def __str__(self):
        return "Terrain%s" % self.__dict__

    def render(self, show_ranges=False):
        """ Call a terrain renderer to render itself.

        Parameters
        ----------
        show_ranges : bool
            Whether to show demon ranges.

        """
        TerrainRenderer(self).render(show_ranges=show_ranges)

    def walkable(self, *positions):
        """Compute walkable tiles.

        Parameters
        ----------
        positions : List[hoplite.utils.HexagonalCoordinates]
            Candidate tiles.

        Returns
        -------
        List[hoplite.utils.HexagonalCoordinates]
            Subset of `positions` only containing tiles a player can currently
            walk on (ie. not over magma or an altar).

        """
        result = list()
        for pos in positions:
            if self.surface.get(pos) != Tile.GROUND:
                continue
            # if pos == self.altar:
            #     continue
            result.append(pos)
        return result

    def pathfind(self, start, goal):
        """Pathfinding between two tiles using the A* algorithm with norm-inf
        distance as heuristic.

        Parameters
        ----------
        start : hoplite.utils.HexagonalCoordinates
            Starting position.
        goal : hoplite.utils.HexagonalCoordinates
            Target position.

        Returns
        -------
        List[hoplite.utils.HexagonalCoordinates]
            Path from `start` to `goal`, both included.

        """

        open_set = {start}
        came_from = dict()
        cost = dict()
        heuristic = dict()
        for pos in hoplite.utils.SURFACE_COORDINATES:
            cost[pos] = float("inf")
            heuristic[pos] = float("inf")
        cost[start] = 0.
        heuristic[start] = (goal - start).norm()
        while len(open_set) > 0:
            # TODO: use heapq to represent the open_set
            current = min(open_set, key=lambda node: heuristic[node])
            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.insert(0, current)
                return path
            open_set.remove(current)
            for neighbor in self.walkable(*hoplite.utils.hexagonal_neighbors(current)):
                tentative_cost = cost[current] + 1
                if tentative_cost < cost[neighbor]:
                    came_from[neighbor] = current
                    cost[neighbor] = tentative_cost
                    heuristic[neighbor] = tentative_cost + \
                        (goal - neighbor).norm()
                    open_set.add(neighbor)
        return None


class Sprite(pygame.Surface):  # pylint: disable=E0239, R0903
    """Square surface showing a sprite loaded from a file.

    Parameters
    ----------
    path : str
        Path to the sprite file.

    Attributes
    ----------
    SURFLAGS : int
        `pygame` flags for handling the surface.
    WIDTH : int
        Pixel width of the sprite.
    HEIGHT : int
        Pixel height of the sprite.
    path

    """

    WIDTH = 32
    HEIGHT = 28

    SURFLAGS = pygame.SRCALPHA | pygame.DOUBLEBUF | pygame.HWSURFACE  # pylint: disable=E1101

    def __init__(self, path):
        pygame.Surface.__init__(  # pylint: disable=W0233
            self,
            (Sprite.WIDTH, Sprite.HEIGHT),
            self.SURFLAGS,
            32
        )
        self.path = path

    def load(self):
        """Load the sprite file and blit it to the internal surface.
        """
        if self.path is not None:
            self.blit(pygame.image.load(self.path).convert_alpha(), (0, 0))


class TerrainRenderer:  # pylint: disable=R0903
    """Create a Pygame window to display a simplified version of the game
    terrain.

    Parameters
    ----------
    terrain : Terrain
        Terrain to render.

    Attributes
    ----------
    tile_width : int
        Pixel width of a tile when rendered. May differ from `Sprite.WIDTH`.
    tile_height : int
        Pixel height of a tile when rendered. May differ from `Sprite.HEIGHT`.
    screen_width : int
        Pygame window width in pixels.
    screen_height : int
        Pygame window height in pixels.
    sprites : dict[SurfaceElement, Sprite]
        Registry of sprites used to render each possible surface element.
    font : pygame.font.Font
        Font used to render coordinates. `None` before it is initialized.
    terrain

    """

    def __init__(self, terrain):
        self.tile_width = 64
        self.tile_height = 64
        self.screen_width = 800
        self.screen_height = 800
        self.sprites = {
            SurfaceElement.GROUND:
                Sprite("assets/ground.png"),
            SurfaceElement.MAGMA:
                Sprite("assets/magma.png"),
            SurfaceElement.FOOTMAN:
                Sprite("assets/footman.png"),
            SurfaceElement.ARCHER:
                Sprite("assets/archer.png"),
            SurfaceElement.DEMOLITIONIST_HOLDING_BOMB:
                Sprite("assets/demolitionist_holding_bomb.png"),
            SurfaceElement.DEMOLITIONIST_WITHOUT_BOMB:
                Sprite("assets/demolitionist_without_bomb.png"),
            SurfaceElement.WIZARD_CHARGED:
                Sprite("assets/wizard_charged.png"),
            SurfaceElement.WIZARD_DISCHARGED:
                Sprite("assets/wizard_discharged.png"),
            SurfaceElement.SPEAR:
                Sprite("assets/spear.png"),
            SurfaceElement.BOMB:
                Sprite("assets/bomb.png"),
            SurfaceElement.PLAYER:
                Sprite("assets/player.png"),
            SurfaceElement.STAIRS:
                Sprite("assets/stairs.png"),
            SurfaceElement.ALTAR_ON:
                Sprite("assets/altar_on.png"),
            SurfaceElement.ALTAR_OFF:
                Sprite("assets/altar_off.png"),
            SurfaceElement.FLEECE:
                Sprite("assets/fleece.png"),
            SurfaceElement.PORTAL:
                Sprite("assets/portal.png"),
        }
        self.terrain = terrain
        self.font = None

    def _render_sprite(self, screen, key, pos):
        column, row = pos.doubled()
        sprite = pygame.transform.scale2x(self.sprites[key])
        screen.blit(sprite, (
            int(self.tile_width * column) +
            (self.screen_width - sprite.get_width()) // 2,
            int(-self.tile_height * row) +
            (self.screen_height - sprite.get_height()) // 2,
        ))

    def _render_coordinates(self, screen, pos):
        column, row = pos.doubled()
        text = self.font.render(str(pos), True, (255, 255, 255))
        screen.blit(text, (
            int(self.tile_width * column) +
            (self.screen_width - text.get_width()) // 2,
            int(-self.tile_height * row) +
            (self.screen_height - text.get_height()) // 2,
        ))

    def _render_ranges(self, screen):
        for demon_pos, demon in self.terrain.demons.items():
            range_surface = pygame.Surface(  # pylint: disable=E1121
                (screen.get_width(), screen.get_height()),
                pygame.SRCALPHA,  # pylint: disable=E1101
                32
            ).convert_alpha()
            demon_color = {
                hoplite.game.demons.DemonSkill.FOOTMAN: (255, 255, 0, 70),
                hoplite.game.demons.DemonSkill.ARCHER: (0, 255, 0, 70),
                hoplite.game.demons.DemonSkill.DEMOLITIONIST: (255, 0, 0, 70),
                hoplite.game.demons.DemonSkill.WIZARD: (0, 0, 255, 70)
            }[demon.skill]
            for pos in demon.range(self.terrain, demon_pos):
                column, row = pos.doubled()
                position = (
                    int(self.tile_width * column) + self.screen_width // 2,
                    int(-self.tile_height * row) + self.screen_height // 2,
                )
                draw_regular_polygon(range_surface, demon_color, 6, 32, position)
            screen.blit(range_surface, (0, 0))

    def render(self, show_ranges=False):
        """Create a Pygame window, blit the terrain, and wait for a quit event.

        Parameters
        ----------
        show_ranges : bool
            Whether to show demons ranges

        """
        pygame.init()  # pylint: disable=E1101
        screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.DOUBLEBUF | pygame.HWSURFACE  # pylint: disable=E1101
        )
        for sprite in self.sprites.values():
            sprite.load()
        pygame.display.set_caption("Hoplite")
        pygame.display.set_icon(pygame.image.load("assets/icon.png"))
        self.font = pygame.font.SysFont("consolas", 10)
        screen.fill((25, 25, 25))
        for pos, elt in zip(hoplite.utils.SURFACE_COORDINATES, self.terrain.to_list()):
            self._render_sprite(screen, elt, pos)
        if show_ranges:
            self._render_ranges(screen)
        for pos in hoplite.utils.SURFACE_COORDINATES:
            self._render_coordinates(screen, pos)
        pygame.display.flip()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # pylint: disable=E1101
                    running = False
