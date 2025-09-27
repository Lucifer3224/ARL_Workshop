#!/usr/bin/env python3
"""shapeNode: Publishes the desired shape or stop command.

This node accepts user input (when a TTY is available) or parameter updates,
then publishes a std_msgs/String on the topic 'shape_cmd' with one of:
  - 'aquarius' | 'rainbow' | 'cap' | 'stop' | 'clear'

Parameters:
  - interactive (bool, default: True): if True and stdin is a TTY, prompt user.
  - shape (string, default: ''): setting this param publishes its value once.

Usage (interactive):
  ros2 launch turtle_shapes shape_commander_launch.py
  # then in another terminal
  ros2 run turtle_shapes shape_node
  # then in the same terminal type one of {aquarius|rainbow|cap|stop|clear|quit}

Usage (parameter-driven):
  ros2 launch turtle_shapes shape_commander_launch.py
  # then in another terminal
  ros2 param set /shape_node shape rainbow {or any other shape|clear|stop}
"""

import sys
from typing import List

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import String


VALID_SHAPES: List[str] = ["aquarius", "rainbow", "cap", "stop", "clear"]


class ShapeNode(Node):
    def __init__(self):
        super().__init__('shape_node')
        self.declare_parameter('interactive', True)
        self.declare_parameter('shape', '')

        self.pub = self.create_publisher(String, 'shape_cmd', 10)

        # React to parameter updates
        self.add_on_set_parameters_callback(self._on_params)

        interactive = self.get_parameter('interactive').get_parameter_value().bool_value
        if interactive and sys.stdin and sys.stdin.isatty():
            # Use a timer to avoid blocking rclpy executor
            self.timer = self.create_timer(0.1, self._poll_stdin)
        else:
            shape = self.get_parameter('shape').get_parameter_value().string_value
            if shape:
                self._publish_shape(shape)

    def _on_params(self, params: List[Parameter]):
        for p in params:
            if p.name == 'shape' and p.type_ == Parameter.Type.STRING:
                self._publish_shape(p.value)
        return SetParametersResult(successful=True)

    def _poll_stdin(self):
        try:
            # Non-blocking line read by checking if input is available
            # Fallback: use blocking input() but only once per timer call if line ready
            import select
            if select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline()
                if not line:
                    return
                cmd = line.strip().lower()
                if cmd in ('q', 'quit', 'exit'):
                    rclpy.shutdown()
                    return
                self._publish_shape(cmd)
        except Exception as e:
            self.get_logger().error(f'stdin read error: {e}')

    def _publish_shape(self, cmd: str):
        cmd = cmd.strip().lower()
        if cmd not in VALID_SHAPES:
            return
        msg = String()
        msg.data = cmd
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ShapeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
