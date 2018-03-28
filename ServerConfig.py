class ServerConfig:

    def __init__(self, host, port, db_path, additional_ports):
        self.host = host
        self.port = port
        self.db_path = db_path
        self.additional_ports = additional_ports


    def get_port(self):
        return self.port
    def set_port(self, port):
        self.port = port

    def get_db_path(self):
        return self.db_path
    def set_db_path(self, db_path):
        self.db_path = db_path

    def get_additional_ports(self):
        return self.additional_ports
    def set_additional_ports(self, additional_ports):
        self.additional_ports = additional_ports

    def get_hostname(self):
        return self.host

    def set_hostname(self, hostname):
        self.hostname = hostname