from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    #routing_service=LaunchConfiguration('server')
    loadGraph=LaunchConfiguration('graph')
    loadAndRoute=LaunchConfiguration("loadAndRoute")

    arg_waypointgraph = DeclareLaunchArgument(
        'graph', default_value='test_run/sample_data/waypointgraph.json', description='Load Waypointgraph'
    )
    arg_tasksAndVehicles = DeclareLaunchArgument(
        'loadAndRoute', default_value='test_run/sample_data/task_data.json', description='Load task and vehicles and then route'
    )
    
    return LaunchDescription([
        #arg_waypointgraph,
        #arg_tasksAndVehicles,
        Node(
            package='routing_agent',
            namespace=loadGraph,
            executable='loadGraph',
            name='loadGraph',
            parameters=[{'file_path': arg_waypointgraph}],
            #arguments=["test_run/sample_data/waypointgraph.json"],
        ),
        Node(
            package='routing_agent',
            namespace='loadAndRoute',
            executable='loadAndRoute',
            #arguments=["test_run/sample_data/task_data.json","test_run/sample_data/vehicle_data.json"],
            name='sim',
        ),

    ])