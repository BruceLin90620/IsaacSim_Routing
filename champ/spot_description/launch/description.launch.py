
import os

import launch_ros
from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    use_sim_time = LaunchConfiguration("use_sim_time")
    description_path = LaunchConfiguration("description_path")

    declare_use_sim_time = DeclareLaunchArgument("use_sim_time", default_value="false", description="Use simulation (Gazebo) clock if true")

    pkg_dir = get_package_share_directory('spot_description')
    urdf_path = os.path.join(pkg_dir, 'urdf', 'spot.urdf')
    urdf = open(urdf_path).read()

    # robot_state_publisher_node = Node(
    #     package="robot_state_publisher",
    #     executable="robot_state_publisher",
        
    #     parameters=[
    #         {"robot_description": urdf},
    #         {"use_tf_static": False},
    #         {"publish_frequency": 200.0},
    #         {"ignore_timestamp": True},
    #         {'use_sim_time': use_sim_time}
    #         ],
    #     # remappings=(("robot_description", "robot_description")),
    # )

    return LaunchDescription(
        [
            declare_use_sim_time,
            # robot_state_publisher_node,
        ]
    )
