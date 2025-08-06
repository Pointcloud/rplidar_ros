#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory #type: ignore
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, EmitEvent  #type: ignore
from launch.event_handlers import OnProcessStart, OnShutdown #type: ignore
from launch.substitutions import LaunchConfiguration  #type: ignore
from launch_ros.actions import LifecycleNode  #type: ignore
from launch_ros.event_handlers import OnStateTransition #type: ignore
from launch_ros.events.lifecycle import ChangeState  #type: ignore
from lifecycle_msgs.msg import Transition  #type: ignore


def generate_launch_description():
    """
    Generate a launch description for the RPLIDAR C1 node with lifecycle management.
    
    This launch file starts the RPLIDAR node as a lifecycle node and manages its state
    transitions to configure and activate it upon startup.
    """
    # Declare launch arguments for RPLIDAR configuration
    channel_type = LaunchConfiguration('channel_type', default='serial')
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB0')
    serial_baudrate = LaunchConfiguration('serial_baudrate', default='460800')
    frame_id = LaunchConfiguration('frame_id', default='lidar_link')
    inverted = LaunchConfiguration('inverted', default='false')
    angle_compensate = LaunchConfiguration('angle_compensate', default='true')
    scan_mode = LaunchConfiguration('scan_mode', default='Standard')
    scan_frequency = LaunchConfiguration('scan_frequency', default='10.0')
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    # Define the lifecycle node for the RPLIDAR
    rplidar_node = LifecycleNode(
        package='rplidar_ros',
        executable='rplidar_node',
        name='rplidar_node',
        parameters=[{
            'channel_type': channel_type,
            'serial_port': serial_port,
            'serial_baudrate': serial_baudrate,
            'frame_id': frame_id,
            'inverted': inverted,
            'angle_compensate': angle_compensate,
            'scan_mode': scan_mode,
            'scan_frequency': scan_frequency,
            'use_sim_time': use_sim_time
        }],
        namespace='',
        output='screen'
    )

    # Event handler to request the 'configure' transition after the node starts
    register_event_handler_for_configure = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=rplidar_node,
            on_start=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=lambda node: node == rplidar_node,
                        transition_id=Transition.TRANSITION_CONFIGURE,
                    ),
                ),
            ],
        )
    )

    # Event handler to request the 'activate' transition after the node is configured
    register_event_handler_for_activate = RegisterEventHandler(
        event_handler=OnStateTransition(
            target_lifecycle_node=rplidar_node,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=lambda node: node == rplidar_node,
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    ),
                ),
            ],
        )
    )

    # Add the shutdown event handler
    shutdown_event_handler = RegisterEventHandler(
        event_handler=OnShutdown(
            on_shutdown=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=lambda node: node == rplidar_node,
                        transition_id=Transition.TRANSITION_ACTIVE_SHUTDOWN,
                    )
                ),
            ]
        )
    )

    # Create the launch description and add the components
    ld = LaunchDescription()

    # Add launch arguments
    ld.add_action(DeclareLaunchArgument('channel_type', default_value='serial', description='Specifying channel type of lidar'))
    ld.add_action(DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0', description='Specifying usb port to connected lidar'))
    ld.add_action(DeclareLaunchArgument('serial_baudrate', default_value='460800', description='Specifying usb port baudrate to connected lidar'))
    ld.add_action(DeclareLaunchArgument('frame_id', default_value='lidar_link', description='Specifying frame_id of lidar'))
    ld.add_action(DeclareLaunchArgument('inverted', default_value='false', description='Specifying whether or not to invert scan data'))
    ld.add_action(DeclareLaunchArgument('angle_compensate', default_value='true', description='Specifying whether or not to enable angle_compensate of scan data'))
    ld.add_action(DeclareLaunchArgument('scan_mode', default_value='Standard', description='Specifying scan mode of lidar'))
    ld.add_action(DeclareLaunchArgument('scan_frequency', default_value='10.0', description='Specifying scan frequency of lidar (Hz)'))
    ld.add_action(DeclareLaunchArgument('use_sim_time', default_value='false', description='Use simulation (Gazebo) clock if true'))

    # Add the lifecycle node and event handlers
    ld.add_action(rplidar_node)
    ld.add_action(register_event_handler_for_configure)
    ld.add_action(register_event_handler_for_activate)
    ld.add_action(shutdown_event_handler)

    return ld
