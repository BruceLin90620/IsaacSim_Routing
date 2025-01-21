#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, Point
from std_srvs.srv import Trigger
from visualization_msgs.msg import MarkerArray, Marker
from std_msgs.msg import ColorRGBA
import json
import os
from datetime import datetime
import argparse

class PoseCollector(Node):
    def __init__(self, map_name):
        super().__init__('pose_collector')
        
        # Store map name for ID generation
        self.map_name = map_name.zfill(3)
        
        # Subscribe to initial pose topic
        self.subscription = self.create_subscription(
            PoseWithCovarianceStamped,
            'initialpose',
            self.pose_callback,
            10
        )
        
        # Create a service for saving the file
        self.srv = self.create_service(
            Trigger,
            'save_waypoints',
            self.save_service_callback
        )

        # Create publisher for visualization markers
        self.marker_publisher = self.create_publisher(
            MarkerArray,
            'waypoint_markers',
            10
        )
        
        # Store collected poses
        self.poses = {}
        self.pose_count = 0
        self.edge_count = 0
        
        # Initialize marker array
        self.marker_array = MarkerArray()
        
        self.get_logger().info(f'Pose collector node started for map {self.map_name}. Ready to collect poses from Rviz2...')
        self.get_logger().info('Use "ros2 service call /save_waypoints std_srvs/srv/Trigger" to save the waypoints.')

    def create_waypoint_marker(self, waypoint_id, position):
        # Create sphere marker
        sphere_marker = Marker()
        sphere_marker.header.frame_id = "map"
        sphere_marker.header.stamp = self.get_clock().now().to_msg()
        sphere_marker.ns = "waypoints"
        sphere_marker.id = hash(waypoint_id) % 2147483647
        sphere_marker.type = Marker.SPHERE
        sphere_marker.action = Marker.ADD
        
        # Set position
        sphere_marker.pose.position.x = position[0]
        sphere_marker.pose.position.y = position[1]
        sphere_marker.pose.position.z = 0.0
        sphere_marker.pose.orientation.w = 1.0
        
        # Set scale
        sphere_marker.scale.x = 0.3
        sphere_marker.scale.y = 0.3
        sphere_marker.scale.z = 0.3
        
        # Set color (blue)
        sphere_marker.color = ColorRGBA()
        sphere_marker.color.r = 0.0
        sphere_marker.color.g = 0.0
        sphere_marker.color.b = 1.0
        sphere_marker.color.a = 1.0

        # Create text marker for ID
        text_marker = Marker()
        text_marker.header.frame_id = "map"
        text_marker.header.stamp = self.get_clock().now().to_msg()
        text_marker.ns = "waypoint_labels"
        text_marker.id = hash(waypoint_id + "_text") % 2147483647
        text_marker.type = Marker.TEXT_VIEW_FACING
        text_marker.action = Marker.ADD
        
        text_marker.pose.position.x = position[0]
        text_marker.pose.position.y = position[1]
        text_marker.pose.position.z = 0.3
        text_marker.pose.orientation.w = 1.0
        
        text_marker.text = waypoint_id
        text_marker.scale.z = 0.3
        
        text_marker.color.r = 0.0
        text_marker.color.g = 0.0
        text_marker.color.b = 0.0
        text_marker.color.a = 1.0
        
        return [sphere_marker, text_marker]

    def create_edge_marker(self, edge_id, start_pos, end_pos):
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "edges"
        marker.id = edge_id
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        
        # Add start and end points
        point_start = Point()
        point_start.x = start_pos[0]
        point_start.y = start_pos[1]
        point_start.z = 0.0
        
        point_end = Point()
        point_end.x = end_pos[0]
        point_end.y = end_pos[1]
        point_end.z = 0.0
        
        marker.points = [point_start, point_end]
        
        # Set scale (line width)
        marker.scale.x = 0.05
        
        # Set color (white with transparency)
        marker.color = ColorRGBA()
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        marker.color.a = 0.8
        
        return marker
        
    def pose_callback(self, msg):
        # Generate unique ID for new pose
        pose_id = f"{self.map_name}_{self.pose_count:03d}"
        
        # Extract position
        position = msg.pose.pose.position
        
        # Create new pose entry
        self.poses[pose_id] = {
            "edges": [],
            "local_location": [
                float(position.x),
                float(position.y),
                0.0
            ]
        }
        
        # Create visualization markers for the new pose
        markers = self.create_waypoint_marker(pose_id, self.poses[pose_id]["local_location"])
        self.marker_array.markers.extend(markers)
        
        # Check alignment and update edges
        self.update_edges_for_new_point(pose_id)
        
        # Publish updated markers
        self.marker_publisher.publish(self.marker_array)
        
        self.pose_count += 1
        self.get_logger().info(f'Received new pose: {pose_id} at position: [{position.x:.3f}, {position.y:.3f}]')

    def check_aligned(self, p1, p2, position_threshold=0.3, distance_threshold=2.5):
        x_aligned = abs(p1[0] - p2[0]) < position_threshold
        y_aligned = abs(p1[1] - p2[1]) < position_threshold
        distance = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
        return (x_aligned or y_aligned) and distance < distance_threshold
        
    def update_edges_for_new_point(self, new_point_id):
        new_pos = self.poses[new_point_id]["local_location"]
        
        for existing_id, existing_data in self.poses.items():
            if existing_id == new_point_id:
                continue
                
            if self.check_aligned(new_pos, existing_data["local_location"]):
                self.poses[new_point_id]["edges"].append(existing_id)
                self.poses[existing_id]["edges"].append(new_point_id)
                
                # Create edge marker
                edge_marker = self.create_edge_marker(
                    self.edge_count,
                    new_pos,
                    existing_data["local_location"]
                )
                self.marker_array.markers.append(edge_marker)
                self.edge_count += 1
                
                self.get_logger().info(f'Added edge between aligned points {new_point_id} and {existing_id}')

    def save_service_callback(self, request, response):
        try:
            if self.pose_count > 0:
                filename = self.save_to_file()
                response.success = True
                response.message = f'Successfully saved {self.pose_count} poses to {filename}'
            else:
                response.success = False
                response.message = 'No poses collected yet'
        except Exception as e:
            response.success = False
            response.message = f'Failed to save file: {str(e)}'
        return response
        
    def save_to_file(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'waypointgraph_{self.map_name}_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(self.poses, f, indent=2)
        
        self.get_logger().info(f'Saved {self.pose_count} poses to {filename}')
        return filename

def main():
    parser = argparse.ArgumentParser(description='Collect waypoints from Rviz2')
    parser.add_argument('map_name', type=str, help='Map identifier (will be used as XXX in point IDs XXX_YYY)')
    args = parser.parse_args()
    
    rclpy.init()
    node = PoseCollector(args.map_name)
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node.pose_count > 0:
            node.save_to_file()
            print("\nSaved waypoints file before shutting down.")
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
