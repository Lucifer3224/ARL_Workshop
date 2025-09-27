from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # Turtlesim window
        Node(package='turtlesim', executable='turtlesim_node', name='turtlesim'),
        # Shape input node
        Node(package='turtle_shapes', executable='shape_node', name='shape_node'),
        # Commander that draws selected shape with turtle1
        Node(package='turtle_shapes', executable='turtle_commander', name='turtle_commander',
             parameters=[{'turtle': 'turtle1', 'auto_clear': True, 'spawn_if_missing': True}]),
    ])
