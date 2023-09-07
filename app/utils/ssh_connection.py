from enum import Enum

from paramiko import RSAKey, SSHClient, AutoAddPolicy, SSHException


class SSHConnection(SSHClient):

    def __init__(self, hostname, username=None, password=None, pkfile=None, port=22):
        """

        :param hostname:
        :param username:
        :param password:
        :param pkfile:
        :param port:
        """
        try:

            SSHClient.__init__(self)
            self.set_missing_host_key_policy(AutoAddPolicy())

            if username and password:
                self.connect(hostname, username=username,
                             password=password, port=port)
            elif pkfile:
                k = RSAKey.from_private_key_file(pkfile, password='testest')
                self.connect(hostname, username=username, pkey=k)

            else:
                raise SSHException

            print('connected')
        except SSHException as e:
            print("Error connecting to %s: %s" % (hostname, e))
            raise SSHException

        self.status = 'available'

    def run_command(self, command):
        """
        Running command and returning the stdout to the invoker
        :param command:
        :return:
        """

        # make status busy
        self.status = "busy"
        try:
            stdin, stdout, stderr = self.exec_command(command)
            # just for test
            print(type(stdin))
            print(type(stdout))
            print(type(stderr))

            if stdout.channel.recv_exit_status() == 0:

                print(f'STDOUT: {stdout.read().decode("utf8")}')
                output = stdout.read().decode("utf8")

            else:
                print(f'STDERR: {stderr.read().decode("utf8")}')
                output = False

            # CLOSING STD FILE OBJECTS
            stdin.close()
            stdout.close()
            stderr.close()
        except SSHException:
            print('it went wrong')
            raise SSHException

        finally:
            # change back to available
            self.status = "available"

        return output

    def __del__(self):
        """
        Closes connection before the deletion of client
        :return:
        """

        try:
            self.close()
        except SSHException:
            print(f'Close connection failed, error')

    ###OPTIONAL###
    def call_shell(self):
        """
        Invkes a shell from the connection to the invoker
        command sending and output receiving is done where the shell is invoked

        :return:
        """
        try:
            shell = self.invoke_shell()
            shell.recv(1024)
        except SSHException:
            print(f"could not invoke shell")
        return shell
