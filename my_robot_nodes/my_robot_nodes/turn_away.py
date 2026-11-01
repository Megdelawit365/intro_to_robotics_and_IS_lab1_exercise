import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus
from my_robot_interfaces.srv import SetTurnSpeed
from std_srvs.srv import SetBool

class TurnAway(Node):
    def __init__(self):
        super().__init__('turn_away')
        
        self.declare_parameter('forward_speed', 0.2)
        self.declare_parameter('turn_speed', 0.5)
        self.declare_parameter('max_turn_speed', 1.5)
        
        self.is_enabled = False 
        
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_publisher_ = self.create_publisher(RobotStatus, '/robot_status', 10)
        
        self.subscription = self.create_subscription(
            ObstacleInfo,
            '/obstacle',
            self.listener_callback,
            10)
            
        self.srv_enable = self.create_service(SetBool, '/turn_away_enable', self.enable_callback)
        self.srv_speed = self.create_service(SetTurnSpeed, '/set_turn_speed', self.speed_callback)
        
        self.get_logger().info('Turn away node started (OFF by default)')

    def enable_callback(self, request, response):
        self.is_enabled = request.data
        if not self.is_enabled:
            self.publisher_.publish(Twist())
            status = RobotStatus()
            status.state = "stopped"
            self.status_publisher_.publish(status)
            
        response.success = True
        response.message = "Enabled" if self.is_enabled else "Disabled"
        return response

    def speed_callback(self, request, response):
        max_speed = self.get_parameter('max_turn_speed').value
        
        if request.turn_speed <= 0.0 or request.turn_speed > max_speed:
            response.success = False
            response.message = f"Rejected: speed must be > 0 and <= {max_speed}"
        else:
            self.set_parameters([rclpy.parameter.Parameter('turn_speed', rclpy.Parameter.Type.DOUBLE, request.turn_speed)])
            response.success = True
            response.message = f"Accepted: speed set to {request.turn_speed}"
        return response

    def listener_callback(self, msg):
        status = RobotStatus()
        status.obstacle_distance = msg.distance
        
        if not self.is_enabled:
            status.state = "stopped"
            self.status_publisher_.publish(status)
            return

        forward_speed = self.get_parameter('forward_speed').value
        turn_speed = self.get_parameter('turn_speed').value

        cmd = Twist()
        
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
