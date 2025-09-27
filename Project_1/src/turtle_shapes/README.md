# turtle_shapes

Draw logos in turtlesim using ROS2.

This package provides:
- shape_node: lets the user choose a shape to draw or stop/clear
- turtle_commander: listens to shape_node and draws with turtlesim

## Usage
1. Launch interactive shape selection + turtle commander

```bash
ros2 launch turtle_shapes shape_commander_launch.py
```

2. In another terminal, send a command (when launched, shape_node runs without a TTY):

```bash
ros2 param set /shape_node shape aquarius
ros2 param set /shape_node shape rainbow
ros2 param set /shape_node shape cap
ros2 param set /shape_node shape clear
ros2 param set /shape_node shape stop
```

[demo.webm](https://github.com/user-attachments/assets/2dc33677-15c1-427f-87dd-aa90f1ae5894)
