import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus  

class TurnAway(Node):
    def __init__(self):
        super().__init__('turn_away')
        self.declare_parameter('forward_speed', 0.2)
        self.declare_parameter('turn_speed', 0.5)
        
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_publisher_ = self.create_publisher(RobotStatus, '/robot_status', 10) # New publisher
        
        self.subscription = self.create_subscription(
            ObstacleInfo,
            '/obstacle',
            self.listener_callback,
            10)
        self.get_logger().info('Turn away node started')

    def listener_callback(self, msg):
        forward_speed = self.get_parameter('forward_speed').value
        turn_speed = self.get_parameter('turn_speed').value

        cmd = Twist()
        status = RobotStatus()
        status.obstacle_distance = msg.distance  
        
        if not msg.too_close:
            cmd.linear.x = forward_speed
            cmd.angular.z = 0.0
            status.state = "forward" 
        else:
            cmd.linear.x = 0.0
            if msg.angle > 0:
                cmd.angular.z = -turn_speed
            else:
                cmd.angular.z = turn_speed
            status.state = "turning" 
                
        self.publisher_.publish(cmd)
        self.status_publisher_.publish(status) 

def main(args=None):
    rclpy.init(args=args)
    node = TurnAway()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
