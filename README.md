# ![Hoplite Icon](assets/icon.png) Hoplite

An attempt at making a basic AI for the Hoplite Android game.

## Preamble

[Hoplite](http://www.magmafortress.com/p/hoplite.html) is a popular turn-based strategy Android game developed by [Magma Fortress](http://www.magmafortress.com/), originally created in [2013](http://www.roguetemple.com/7drl/2013/). Try it ([there is a free and a premium version](https://play.google.com/store/apps/details?id=com.magmafortress.hoplite&hl=fr)), you will love it!

This modules provides an interface for automatically playing the game on an Android simulator or even live on a device. Screen is captured and analyzed for the program to get a logical representation of the game. Then, like most chess engines, possible moves are explored and evaluated by pondering some relevant features. The best one is picked, and played.

[Here is a demonstration of it working on a emulator](https://www.youtube.com/watch?v=GJIp3fEq9Xc).

This is a first draft, meaning many components are missing or poorly implemented.

![Hoplite Android Icon](https://2.bp.blogspot.com/-QH3Ceormja0/UrKqFsfIMkI/AAAAAAAAAIM/XicUf6o0n4I/s200/helmetICON.png)

## Getting Started

### Prerequisites

You will need Python 3 and Android Studio (for [`adb`](https://developer.android.com/studio/command-line/adb)).

`adb` allows for remotely controlling the Android device (either a real phone plugged into the computer via USB with ['USB debugging' enabled](https://developer.android.com/studio/command-line/adb#Enabling), or an emulated phone created with [AVD](https://developer.android.com/studio/run/managing-avds)).

### Installation

1. Clone the repository

        git clone https://github.com/ychalier/hoplite.git

2. Install the dependencies

        cd hoplite/
        pip install -r requirements.txt

**Disclaimer: interactions with phone screen currently rely on static and hardcoded values. A screen resolution of 1080x1920 is required for them to work properly.** For other resolutions, changes might be required in the following places:

- `vision.observer.ScreenParser.__init__`
- `actuator.hexagonal_to_pixels`
- `actuator.Actuator`

### Usage

1. Either start the emulated phone in AVD or plug in your phone, and open the Hoplite app.
2. List the available devices with

        adb devices 

3. Start the script with:

        python main.py play <adb-device-id>

Use `python main.py --help` for more details.

## Contributing

Open pull requests or issues if you have any proposition to make. I put some screenshots [here](https://mega.nz/folder/2L5TnJLC#70yL5fUOErmTHBo9SUD2Nw) (2MB) helping development, and the [templates](https://mega.nz/folder/LCgFUYaD#P4OjM9CjsMTVFGx_TDo-Aw) (1MB) used for the classifiers.

If you implement some features, please make sure your code is clean enough (for this matter I use the [Pylint](https://www.pylint.org/) linter) and documented enough (add docstrings with short descriptions, types of arguments and returned values). I use [pdoc](https://pdoc3.github.io/pdoc/) to generate the documentation.

## Note

For some reason, screen observation seems broken. Classifiers need to be retrained. This branch provides a temporary fix where the classifier tolerance is increased. Here is a quick status:

- Terrain observation seems fine
- Health & Cooldown status seem fine
- Clicking on "Embark" button seems broken
- Energy detection seems broken
- Altar interaction is broken, and has been disabled (along with incentives to reach the altar) to avoid crashes

After a quick test, the current script reached depth 8, without prayers and jumps.