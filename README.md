# Sports Replay

## Description

is an open source autonomous indoor football/basketball/handball video recording solution.
It requires two 110 degree wide angle cameras installed in two opposite (longest diagonal) corners.
Besides two cameras it also requires one Jetson Nano, and one Raspberry Pi 4.

To match your use case you need to amend setup file sports-replay.ini which can be found in Shared folder.
To prevent certain parts of the video to be used for ball detection, you need to provide the array of restricted, or array of allowed polygons, as shown in polygons.json (Shared folder).

For more information, please open GitHub issue.

## Cloning this repository
`mkdir $HOME/GitHub`

`cd $HOME/GitHub`

`git clone https://github.com/HEBOS/SportsReplay.git sports-replay`

## Configuring Devices

[Common Instructions - read this first](docs/COMMON.md)

[Configuring the Router](docs/ROUTER.md)

[Configuring Jetson Nano](docs/JETSON.md)

[Configuring Raspberry Pi](docs/RASPBERRY.md)

[Configuring the camera](docs/CAMERA.md)
