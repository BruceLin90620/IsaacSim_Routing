Graph based routing engine with switch map engine which build with ROS ecosystem.
Can coupled with Nav2 later on. 

# Setup and Execution Instructions

## 1. Build the Workspace

Navigate to your ROS workspace and build the packages:

```bash
colcon build --packages-select routing_agent routing_agent_interfaces
```

## 2. Run the Server

Start the routing agent server:

```bash
ros2 run routing_agent server
```

## 2-1. Execute the Routing Agent with simple 'ros2 launch'

### b. Launch

```bash
ros2 launch routing_agent runServer.launch.py
```

## 4-2. Execute the Routing Agent with old fashion 'ros2 run'

### a. Open a New Terminal Window and Navigate to the ROS Workspace

You should choose either b or c to execute.

### b. Load the Waypoint Graph

Load the global waypoint graph by specifying the path to your graph file:

```bash
ros2 run routing_agent loadGraph <path_to_your_global_graph_file.json>
```

### c. Merge the Waypoint Graph

Merge additional graph files by specifying the path to the configuration file:

```bash
ros2 run routing_agent mergeGraph <path_to_your_graph_files_config.config.json>
```

### d. Load Tasks and Vehicles

Load task data and vehicle data by specifying the paths to the respective JSON files:

```bash
ros2 run routing_agent routingClient <path_to_your_task_data.json> <path_to_your_vehicle_data.json>
```

### e. Communicate with Navigation

To communicate with the navigation system, use the following commands. Replace `<T or F>` with `T` (true) or `F` (false), and `<global_location>` with the specific location (e.g., `000_000`).

- Navigate to the location with `T`:

    ```bash
    ros2 run routing_agent nav T 000_000
    ```

- Navigate to the location with `F`:

    ```bash
    ros2 run routing_agent nav F 000_000
    ```


# Features
1.Routing Engine (Server)

  1. Single Agent Task Assign (TSP)
  2. Pathfinding (Dijkstra)
  3. WaypointGraph Data format

2. Switch Map Server


# Code Format Guidelines
1. FileName:
  template_data_format
2. functionName
3. SelfDefinedData
4. parameterisparameter
5. localVariableName
6. globalVariableName
