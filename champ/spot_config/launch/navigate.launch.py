# Copyright (c) 2021 Juan Miguel Jimeno
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def generate_launch_description():
    this_package = FindPackageShare('spot_config')

    default_map_path = PathJoinSubstitution(
        [this_package, 'maps', 'mit_lab.yaml']
    )

    default_params_file_path = PathJoinSubstitution(
        [this_package, 'config/autonomy', 'navigation.yaml']
    )

    nav2_launch_path = PathJoinSubstitution(
        [FindPackageShare('champ_navigation'), 'launch', 'navigate.launch.py']
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            name='map', 
            default_value=default_map_path,
            description='Navigation map path'
        ),
        
        DeclareLaunchArgument(
            name='params_file', 
            default_value=default_params_file_path,
            description='Navigation2 params file'
        ),

        DeclareLaunchArgument(
            name='sim', 
            default_value='true',
            description='Enable use_sime_time to true'
        ),

        DeclareLaunchArgument(
            name='rviz', 
            default_value='false',
            description='Run rviz'
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch_path),
            launch_arguments={
                'map': LaunchConfiguration("map"),
                'params_file': LaunchConfiguration("params_file"),
                'sim': LaunchConfiguration("sim"),
                'rviz': LaunchConfiguration("rviz")
            }.items()
        ),

        Node(
            package='pointcloud_to_laserscan', executable='pointcloud_to_laserscan_node',
            remappings=[('cloud_in', ['/point_cloud']),
                        ('scan', ['/scan'])],
            parameters=[{
                'target_frame': 'rtx_lidar',
                'transform_tolerance': 0.01,
                'min_height': -0.4,
                'max_height': 1.5,
                'angle_min': -1.5708,  # -M_PI/2
                'angle_max': 1.5708,  # M_PI/2
                'angle_increment': 0.0087,  # M_PI/360.0
                'scan_time': 0.3333,
                'range_min': 0.05,
                'range_max': 100.0,
                'use_inf': True,
                'inf_epsilon': 1.0,
                # 'concurrency_level': 1,
            }],
            name='pointcloud_to_laserscan'
            )
    ])
