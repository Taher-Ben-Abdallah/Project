"""
    Pool.nodes=[
    Node={
        'hostname': 127.0.0.1,
        'max_conns': #,
        'services': [],
        'tools': [],
        'username': , 'password': , OR 'pkfile': ,
        'ports': {'ssh':22},
        'connections': [{status: 'available'},{}]
    }
    ]
"""
from paramiko.ssh_exception import SSHException
from werkzeug.exceptions import BadRequest, InternalServerError

from app.models.nodes_pool import NodesPool
from app.utils.ssh_connection import SSHConnection


class ConnectionPool:
    def __init__(self, conns_per_node=10):

        self.platform_services = ['ssh', 'metasploit', 'zap']
        self.conns_per_node = conns_per_node
        self.nodes = []

    def load_nodes(self):
        try:
            self.nodes = NodesPool.get_nodes()
        except InternalServerError:
            print('Inable to load nodes information from database')


    def add_node(self, hostname, username=None, password=None, pkfile=None, ports=None, max_conns=None, services=None):
        """
        Adding node to the list of connexions

        :param hostname:
        :param username:
        :param password:
        :param pkfile:
        :param ports:
        :param max_conns:
        :param services:
        :return:
        """

        # predefined node ports to use for services
        if not ports:
            ports = {
                'ssh': 22 if 'ssh' in services else None,
                'metasploit': 55553 if 'metasploit' in services else None,
                'zap_api': 8080 if 'zap_api' in services else None,
            }

        node = {
            'hostname': hostname,
            'ports': ports,
            'max_conns': max_conns if max_conns is not None else self.conns_per_node,
            'connections': []
        }

        if services:

            node['services'] = services
            if username and password:
                node['username'] = username
                node['password'] = password
            elif pkfile:
                node['pkfile'] = pkfile
            else:
                return False

            self.nodes.append(node)
            return True

        return False

    def delete_node(self, node):
        """
        Deletes a node from the connections pool after finishing tasks at hand
        :param node:
        :return:
        """

        for conn in node['nodes']:
            while conn.status == 'in use':
                continue
            del conn
        self.nodes.remove(node)

    def get_node(self, service):

        if service not in self.platform_services:
            # raise BadRequest
            return None

        node_info = {}
        for node in self.nodes:
            if service in node['services']:
                node_info['hostname'] = node['hostname']
                node_info['username'] = node['username']
                node_info['password'] = node['password']
                node_info['port'] = node['ports'][service]
                break

        return node_info

    def get_ssh_connection(self, tools):
        """
        LOOK FOR NODE WITH SERVICE
        :param tools: list of services
        :return: 
        """

        for node in self.nodes:
            if all(t in node['tools'] for t in tools):
                for connection in node['connections']:
                    if connection.status == 'available':
                        return connection
                if len(node['connections']) < node['max_conns']:
                    connection = SSHConnection(hostname=node['hostname'], username=node['username'],
                                               password=node['password'], port=node['ports']['ssh'])
                    node['connections'].append(connection)
                    return connection

        return None


##### Creation of pool ( to be imported into __init__ ) #####
pool = ConnectionPool(conns_per_node=10)
