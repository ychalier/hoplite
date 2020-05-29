# An Empirical Study of Hoplite's Internal Rules

**Careful: this document if far from being complete.**

## Player

The player is a Greek hoplite.

### Attacks

**Stab**: Stabs are performed automatically based on your movement relative to demons. A demon will be stabbed any time you move between two tiles adjacent to that demon.

**Lunge**: You will lunge automatically whenever moving directly toward a demon. Leaping toward a demon also trigger a lunge attack. Lunge only hits demons you move directly toward. You cannot lunge while your spear is on the ground.

### Moves

A player can be on a tile if it is not magma and if there is no demon, no bomb, and no altar on it. This this tile happens to be the stairs, then the player goes to the next level.

If a player has at least 50 energy, it may consume 50 energy to **leap** over another tile. The **leap distance** is an attribute of the player (2 by default, can be increased with prayers). The player can not leap to an adjacent tile.

#### Energy

A leap costs 50 energy points. Energy is maxed at 100 at the beginning of the game. Here are the different ways of restoring energy points:

1. The prayer "Greater Energy" restores 20 energy points and increases the maximum energy by 20, bringing it to 120.
2. The prayer "Greater Energy II" restores 15 energy points increases the maximum energy by 15, bringing it to 135.
3. If the player moves into a tile with at least one adjacent demon, restore 10 energy points [[source]](http://www.magmafortress.com/2013/09/hoplite-20.html)
4. If a player has the "Bloodlust" prayer, then each kill (throwing the spear, pushing into lava or exploding a bomb count as kills) restores 6 energy points.

A player can **bash** an adjacent tile. This knocks demons and bombs around the bashed tile (by default, only the tile aligned with the player (let's name it A), but this can be expanded into a three-tiles arc centered on A, or even all the tiles adjacent to the bashed one). The **knockback distance** is an attribute of the player (1 by default, can be increased with prayers). If a demon is knocked out of the map surface or onto/through magma, it dies [[source]](http://www.magmafortress.com/2014/07/hoplite-23-progress.html). If there is no room for a demon or a bomb to be knocked, then the game follows [this logic](https://www.reddit.com/r/Hoplite/comments/fxx69q/will_i_fall_into_lava_if_i_bashreaction_how_does/fn9ntxe/?context=3).

A player can **throw** the spear to an adjacent tile, killing any demon it falls on. The **throwing distance** is an attribute of the player (2 by default, can be increased with prayers).

## Demons

Demons are the enemies of the game. **One major challenge is to determine the walking pattern of these demons.**

- **Footman**: A resident of the underworld that is skilled in melee combat. It can only attack adjacent tiles.
- **Archer**: A resident of the underworld that is skilled in ranged combat. It has a maximum range of 5 tiles and cannot attack adjacent tiles. It can only shoot in 6 directions.
- **Demolitionist**: A resident of the underworld that is able to throw bombs. It has a range of 3 tiles. It can only throw a bomb every 3 turn. There are two sprites for the demolitionist: one holding a bomb and another without a bomb. Demolitionists won't throw bombs into tiles adjacent to other demons. ([gamedev's advice](http://www.magmafortress.com/2015/03/hoplite-challenge-mode-is-ready.html))
- **Wizard**: A resident of the underworld that is able to conjure beams of fire. It has a range of 5 tiles and will hit all tiles in range. It will avoid hitting other demons and cannot fire two turns in a row. It can only shoot in 6 directions. There are two sprites for the wizard: one with its wand charged (meaning it can trigger the beam of fire at any time) and one with its wand discharged (after an attack). Wizards won't shoot if their beam would hit a demon behind you. ([gamedev's advice](http://www.magmafortress.com/2015/03/hoplite-challenge-mode-is-ready.html))

Archers and Wizards prefer to be in tiles they can attack you from. You can often predict their movement based on this. ([gamedev's advice](http://www.magmafortress.com/2015/03/hoplite-challenge-mode-is-ready.html))

Those demons may have a **status**, which influences how they behave:

- Shielded
- Sleeping
- Stunned

## Prayers

Prayers can be made at an altar of Apollo (once per depth). Here are available prayers up to depth 16 *(incomplete)*:

- **Divine Restoration**: Heals Completely.
- **Fortitude**: Increases maximum health. (Maximum of 8 hearts)
- **Bloodlust**: Killing restores 6 energy. (Sacrifice: 1)
- **Mighty Bash**: Increases knock back distance.
- **Sweeping Bash**: Affects targets in an arc.
- **Spinning Bash**: Affects all adjacent targets.
- **Quick Bash**: Reduces cooldown.
- **Greater Throw**: Increases throw distance.
- **Greater Throw II**: Increases throw distance. (Sacrifice: 1)
- **Greater Energy**: Increases maximum energy.
- **Greater Energy II**: Increases maximum energy. (Sacrifice: 1)
- **Deep Lunge**: Lunge penetrates through target.
- **Patience**: Allows skipping turns.
- **Surge**: Killing in three consecutive actions restores 100 energy, resets cooldowns and returns your spear. (Sacrifice: 1)
- **Regeneration**: Once per depth, killing in three consecutive actions regenerates health. (Sacrifice: 1)
- **Winged Sandals**: Increases leap distance. (Sacrifice: 1)
- **Staggering Leap**: Stuns adjacent enemies on landing. (Sacrifice: 2)

A player next to an altar can click on that altar to pray. This will count as a turn.
