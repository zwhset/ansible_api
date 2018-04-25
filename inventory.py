# -*- coding: utf-8 -*-

"""
    package.module
    ~~~~~~~~~~~~~~

    Ansible API inventory 主机清单模块

    :copyright: (c) YEAR by zwhset.
    :license: GOMEOPS, see LICENSE_FILE for more details.
"""

from ansible.inventory.host import Host
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader

class BaseHost(Host):
    def __init__(self, host_data):
        """
        初始化主机信息
        :param host_data: format.
            {
                'hostname' : '',
                'ip' : 'ip',
                'port' : 22
                'username' : '',
                'password' : '',
                'private_key' : '',
                'become' : {
                    'method' : '',
                    'user' : '',
                    'pass' : ''
                },
                'groups' : [],
                'vars' : {}
            }
        """
        self.host_data = host_data
        hostname = host_data.get('hostname') or host_data.get('ip')
        port = host_data.get('port', None) or 22
        super(BaseHost, self).__init__(hostname, port)

        # 初始化主机信息与环境变量
        self.__set_required_variables()
        self.__set_extra_variables()

    def __set_required_variables(self):
        """添加主机信息"""

        # append host info
        host_data = self.host_data
        self.set_variable('ansible_host', host_data['ip'])
        self.set_variable('ansible_port', host_data['port'])

        if host_data.get('username', None):
            self.set_variable('ansible_user', host_data['username'])

        # append password or private_key
        if host_data.get('password', None):
            self.set_variable('ansible_ssh_pass', host_data['password'])
        if host_data.get('private_key', None):
            self.set_variable('ansible_ssh_private_key_file', host_data['private_key'])

        # append become
        become = host_data.get('become', None)
        if become:
            self.set_variable('ansible_become', True)
            self.set_variable('ansible_become_method', become.get('method', 'sudo'))
            self.set_variable('ansible_become_user', become.get('user', 'root'))
            self.set_variable('ansible_become_pass', become.get('pass', ''))
        else:
            self.set_variable('ansible_become', False)

    def __set_extra_variables(self):
        """设置主机的环境变量信息"""
        for k, v in self.host_data.get('vars', {}).items():
            self.set_variable(k, v)

    def __repr__(self):
        return self.name

class BaseInventory(InventoryManager):
    """根据给出的组生成inventory对象"""

    loader_class = DataLoader
    variable_manager_class = VariableManager
    host_manager_class = BaseHost

    def __init__(self, host_list=None):
        """
        生成inventory对象
        :param host_list list
            [
                {
                    'hostname' : '',
                    'ip' : 22,
                    'username' : '',
                    'password' : '',
                    'private_key' : '',
                    'become' : {
                        'method' : '',
                        'user' : '',
                        'pass' : ''
                    },
                    'groups' : [],
                    'vars' : {}
                },
                ...
            ]
        """
        if host_list is None:
            host_list = []

        self.host_list = host_list
        assert isinstance(host_list, list)
        self.loader = self.loader_class()
        self.variable_manager = self.variable_manager_class()
        super(BaseInventory, self).__init__(self.loader)

    def get_groups(self):
        """获取所有组"""
        return self._inventory.groups

    def get_group(self, name):
        """按照name获取组"""
        return self._inventory.groups.get(name, None)

    def parse_sources(self, cache=False):
        """解析组"""
        group_all = self.get_group('all')
        ungrouped = self.get_group('ungrouped')

        for host_data in self.host_list:
            host = self.host_manager_class(host_data=host_data)

            # 修改此处为IP也可以走
            try:
                self.hosts[host_data['hostname']] = host
            except:
                self.hosts[host_data['ip']] = host

            groups_data = host_data.get('groups')
            if groups_data:
                for group_name in groups_data:
                    group = self.get_group(group_name)
                    if group is None:
                        self.add_group(group_name)
                        group = self.get_group(group_name)
                    group.add_host(host)
            else:
                ungrouped.add_host(host)
            group_all.add_host(host)

    def get_matched_hosts(self, pattern):
        """按pattern匹配主机"""
        return self.get_hosts(pattern)
