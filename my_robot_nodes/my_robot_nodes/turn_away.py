import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from lab_interfaces.msg import ObstacleInfo

class TurnAway(Node):
    def __init__(self):
        super().__init__('turn_away')
        
        self.declare_parameter('forward_speed', 0.2)
        self.declare_parameter('turn_speed', 0.5)
        
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
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
        
        if not msg.too_close:
            cmd.linear.x = forward_speed
            cmd.angular.z = 0.0
        else:
            cmd.linear.x = 0.0
            if msg.angle > 0:
                cmd.angular.z = -turn_speed
            else:
                cmd.angular.z = turn_speed
                
        self.publisher_.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = TurnAway()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
