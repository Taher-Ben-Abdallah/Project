import nmap
from werkzeug.exceptions import InternalServerError

scan_types = {
    'connect': '-sT',
    'syn': '-sS',
    'ack': '-sA',
    'null': '-sN',
    'fin': '-sF',
    'xmas': '-sX',
    'no_ping': '-Pn',
    # UDP Scan
    'udp': '-sU',
    # Host discovery
    'ping': '-sn',
}

opts = {
    'os': '-O',
    'services': '-sV',
    'all': '-A',
}


def add_ports(ports):
    """

    :param ports: ports to run scan on
    :return: ports to add to the command
    """
    output = ''
    # top ports NOT WORKING
    if 'top-ports' in ports:
        output += f"-top-ports {str(ports['top-ports'])} "
    if 'all-ports' in ports:
        output += '-p- '
    else:
        output += ' -p '
        if 'range' in ports:
            # range is a tuple of two integers
            output += str(ports['range'][0]) + '-' + \
                      str(ports['range'][1]) + ' '
        elif 'list' in ports:
            # list is a list of integers
            output += ','.join(str(port) for port in ports['list']) + ' '
        else:
            if 'tcp_ports' in ports:
                output += 'T:'
                sep = ',' if 'udp_ports' in ports else ' '
                output += ','.join(str(port)
                                   for port in ports['tcp_ports']) + sep
            if 'udp_ports' in ports:
                output += 'U:'
                output += ','.join(str(port)
                                   for port in ports['udp_ports']) + ' '

    return output


# TODO: make it add_args(options,ports,scripts)
def add_args(scan_type=None, options=None, ports=None, scripts=None):
    """

    :param scan_type: name of scan type
    :param options: options to add
    :param ports: ports to scan
    :param scripts: scripts to run when scanning
    :return: the scan command arguments
    """
    args = ''

    if ports:
        args += add_ports(ports)
    if scan_type:
        args += scan_types[scan_type] + ' '
    # -A or -sV
    for option in options:
        if option:
            args += opts[option] + ' '

    if scripts:
        if scripts['list']:
            args += f"--script={'default' if not bool(scripts['list']) else {','.join(s for s in scripts['list'])} } "
        if scripts['args']:
            args += f"--script-args={','.join(a for a in scripts['args'])} "
    # Basic scan
    return args


def run_nmap_scan(targets, scan_type=None, options=None, ports=None, scripts=None):
    """

    :param targets: targets to scan
    :param scan_type: name of scan type
    :param options: options to add
    :param ports:
    :param scripts: scripts to laucnh with scan
    :return:
    """

    nm = nmap.PortScanner()

    # Run the Nmap scan
    nm.scan(hosts=targets, ports=ports, arguments=add_args(
        scan_type=scan_type, options=options, ports=ports, scripts=scripts))

    scan_results = []

    for host in nm.all_hosts():
        host_info = {
            "Host": host,
            "Status": nm[host].state(),
            "OS": {
                'name': nm[host]['osmatch'][0]['name'],
                'type': nm[host]['osmatch'][0]['osclass']['type'],
            } if 'osmatch' in nm[host] else "N/A",

            "Ports": {
                'tcp': [],
                'udp': [],
                'ip': [],
                'sctp': [],
            },
            "Scripts": []
        }

        protocols = nm[host].all_protocols()
        for protocol in protocols:
            # Getting detected port info from scanned host
            for port in nm[host][protocol]:
                port_info = {
                    "Port": port,
                    "State": nm[host][protocol][port]['state'],
                    "Service": nm[host][protocol][port]['name'],
                    "Version": nm[host][protocol][port]['version']
                }
                host_info["Ports"][protocol].append(port_info)

                # Getting all the script results from ports of the scanned host
                for script_id, script_output in nm[host][protocol][port]['script'].items():
                    script_info = {
                        "Port": port,
                        "Script ID": script_id,
                        "Output": script_output
                    }
                    host_info["Scripts"].append(script_info)

        scan_results.append(host_info)

    return scan_results


def host_discovery(subnet):
    try:
        nm = nmap.PortScanner()

        # Perform host discovery ( -sn option, which stands for "No port scan")
        nm.scan(hosts=subnet, arguments="-sn")

        # Extract and return the list of discovered hosts
        discovered_hosts = [host for host in nm.all_hosts()]

        return discovered_hosts

    except nmap.PortScannerError:
        # Handle any errors that may occur during host discovery
        raise InternalServerError
