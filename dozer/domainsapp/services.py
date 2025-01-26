''' domainsapp services.py '''
import re
import os
import socket
from nginxparser.nginxparser import load

def find_proxy_pass(directives):
    """Рекурсивная функция для поиска всех значений proxy_pass в конфигурации."""
    proxy_pass_values = []

    for directive in directives:
        if isinstance(directive, list):
            # Если это вложенный список, проверим первый элемент на 'proxy_pass'
            if directive and directive[0] == 'proxy_pass':
                # Добавляем весь блок директивы, а не только URL
                proxy_pass_values.append(directive[1])
            else:
                # Рекурсивно проверяем вложенные директивы
                proxy_pass_values.extend(find_proxy_pass(directive))

    return proxy_pass_values

def parse_nginx_config(file_path):
    ''' parse '''
    with open(file_path, 'r', encoding='utf-8') as f:
        parsed_config = load(f)

    server_info = {}

    for block in parsed_config:
        if isinstance(block, list) and block[0][0] == 'server':
            domain_name = None
            listen = []
            ip_addresses = []

            for directive in block[1]:
                # Find the domain name
                if directive[0] == 'server_name':
                    domain_name = directive[1].split()[0]  # Take the first domain name

                # Find the listen ports
                if directive[0] == 'listen':
                    listen.append(directive[1].split()[0])

            proxy_pass_values = find_proxy_pass(block)

            for proxy_pass_value in proxy_pass_values:
                # Ищем http:// или https://, за которым идет IP или доменное имя, и опциональный порт
                match = re.search(r'https?://([a-zA-Z0-9.-]+)(?::(\d+))?', proxy_pass_value)  # <-- Измененная строка
                if match:
                    ip = match.group(1)
                    port = match.group(2) if match.group(2) else None

                    # Добавляем IP и порт в server_info, если это IP-адрес
                    try:
                        socket.inet_aton(ip)  # Проверяем, является ли это IP-адресом
                        ip_addresses.append((ip, port))  # Добавляем в список IP:PORT
                    except socket.error:
                        pass  # Игнорируем, если это не IP-адрес

            # Добавить собранную информацию в server_info
            if domain_name:
                if domain_name not in server_info:
                    server_info[domain_name] = []

                # Добавляем информацию о текущем блоке
                server_info[domain_name].append({
                    "listen": listen,
                    "ip_addresses": ip_addresses
                })

    return server_info

def print_server_info(server_info):
    ''' print '''
    for domain, mappings in server_info.items():
        print(f"Domain: {domain}")
        for mapping in mappings:
            listens = ", ".join(mapping.get("listen", [])) or "None"
            ips = ", ".join(f"{ip}:{port}" for ip, port in mapping.get("ip_addresses", [])) or "None"
            print(f"  Listen: {listens}")
            print(f"  IP Addresses: {ips}")

def analyze_all_configs(config_dir):
    ''' Analyze all .conf files in a directory '''
    all_server_data = {}  # Добавляем переменную для накопления результатов
    for root, _, files in os.walk(config_dir):
        for file in files:
            if file.endswith(".conf"):
                config_path = os.path.join(root, file)
                #print(f"\nAnalyzing file: {config_path}\n")
                server_data = parse_nginx_config(config_path)
                #print_server_info(server_data)
                #print(server_data)

                for domain, mappings in server_data.items():
                    if domain not in all_server_data:
                        all_server_data[domain] = []
                    all_server_data[domain].extend(mappings)
    return all_server_data
