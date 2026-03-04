cmake_minimum_required(VERSION 3.1.3)
project(armpi_gripper_moveit_config)

find_package(catkin REQUIRED)

catkin_package()

install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
  PATTERN "setup_assistant.launch" EXCLUDE)
install(DIRECTORY config DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

catkin_install_python(PROGRAMS
  scripts/farsight_moveit_action_server.py  
  scripts/joint_state.py                
  scripts/arm_protocol_test.py 
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
