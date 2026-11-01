from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    diffdrive_dir = get_package_share_directory('diffdrive_bot')
    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(diffdrive_dir, 'launch', 'control.launch.py')
        )
    )

    side_length_arg = DeclareLaunchArgument(
        'side_length',
        default_value='0.5',
        description='Side length of the square in meters'
    )

    rotate_server = Node(
        package='my_robot_nodes',
        executable='rotate_server',
        name='rotate_server'
    )

    square_driver = Node(
        package='my_robot_nodes',
        executable='square_driver',
        name='square_driver',
        parameters=[{'side_length': LaunchConfiguration('side_length')}]
    )

    return LaunchDescription([
        side_length_arg,
        control_launch,
        rotate_server,
        square_driver
    ])
