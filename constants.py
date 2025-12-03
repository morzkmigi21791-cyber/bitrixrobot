from schemas import RobotConfig, RobotProperty

# Настройки робота
DEFAULT_ROBOT_CONFIG = RobotConfig(
    code="REST_ROBOT_MY_UNIQUE_V3",
    name="Bit24Test",
    handler_url="",
    properties={
        "LAST_NAME": RobotProperty(Name="Фамилия", Required=True),
        "NAME": RobotProperty(Name="Имя", Required=True),
        "SECOND_NAME": RobotProperty(Name="Отчество"),
        "PHONE": RobotProperty(Name="Телефон"),
        "EMAIL": RobotProperty(Name="Email")
    },
    return_properties={
        "created_contact_id": RobotProperty(Name="ID созданного контакта", Type="int"),
        "res_name": RobotProperty(Name="Имя контакта", Type="string"),
        "res_last_name": RobotProperty(Name="Фамилия контакта", Type="string"),
        "res_second_name": RobotProperty(Name="Отчество контакта", Type="string"),
        "res_full_name": RobotProperty(Name="ФИО (одной строкой)", Type="string"),
        "res_phone": RobotProperty(Name="Телефон контакта (возврат)", Type="string"),
        "res_email": RobotProperty(Name="Email контакта (возврат)", Type="string")
    }
)