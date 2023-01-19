from datetime import datetime

import paramiko
import time
import socket
from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
import logging
from paramiko.ssh_exception import SSHException


logging.getLogger('paramiko').setLevel(logging.WARNING)

logging.basicConfig(
    format = '%(threadName)s %(name)s %(levelname)s: %(message)s',
    level=logging.INFO,
)


def send_show_command(
    ip,
    username,
    password,
    commands,
    max_bytes=60000,
    short_pause=1,
    long_pause=5,
    read_timeout=10,
                    ):

    try:
        with paramiko.SSHClient() as connect:
            connect.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            connect.connect(
                hostname=ip,
                username=username,
                password=password,
                look_for_keys=False,
                allow_agent=False,
            )
            logging.info(f'Подключаюсь к {ip}')

            with connect.invoke_shell() as session:
                prompt = session.recv(max_bytes).decode('utf-8').replace('\r\n','')
                logging.info(f'Зашёл на {prompt}')
                session.send("terminal length 0\n")
                time.sleep(short_pause)
                #print(session.recv(max_bytes))
                result = {}
                for command in commands:
                    session.send(f"{command}\n")
                    output = read_until(session, max_bytes,prompt, read_timeout)
                    result[command] = output
            return result
    except (OSError, SSHException) as error:  # Для поиска проблем с подключением
        return error

def read_until(session, max_bytes,prompt, read_timeout):
    session.settimeout(read_timeout)
    output = ""
    while True:
        time.sleep(0.2)
        try:
            part = session.recv(max_bytes).decode("utf-8").replace('\r\n', '\n')
            output += part
            time.sleep(0.5)
            if prompt in output:
               break
        except socket.timeout:  # когда ожидаем вывода, но его нет
            break
    return output



def send_command_to_devices(devices, username, password,
                            commands, limit=3):
    result = {}
    tasks_list = []
    with ThreadPoolExecutor(max_workers=limit) as executor:
        for device in devices:
            futures = executor.submit(send_show_command, device, username, password, commands)
            tasks_list.append(futures)
        for ip,task in zip(devices,tasks_list):
            result[ip] = task.result()
    return result



if __name__ == "__main__":
    result={}
    time_start = datetime.now()
    username = 'cisco'
    password = 'cisco'
    devices = ["192.168.139.1", "192.168.139.2", "192.168.139.3"]
    commands = ["sh clock", "sh arp"]
    #for device in devices:
    #    result[device] = send_show_command(device, "cisco", "cisco",  commands)
    pprint(send_command_to_devices(devices, username, password, commands, limit=3), width=120)
    print(f'Скрипт работал {datetime.now()-time_start}')

'''send_show_command(
   ip,
   username,
   password,
   command,
   max_bytes=60000,
   short_pause=1,
   long_pause=5,'''


'''import yaml
from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
import logging
from datetime import datetime
import time

# Этот словарь нужен только для проверки работа кода, в нем можно менять IP-адреса
# тест берет адреса из файла devices.yaml
commands = {
    "192.168.139.3": ["sh ip int br", "sh ip route | ex -"],
    "192.168.139.1": ["sh ip int br", "sh int desc"],
    "192.168.139.2": ["sh int desc"],
}

logging.getLogger('paramiko').setLevel(logging.WARNING)

logging.basicConfig(
    format = '%(threadName)s %(name)s %(levelname)s: %(message)s',
    level=logging.INFO,
)


def send_command_func(device, command):
    with ConnectHandler(**device) as connect:
        result = []
        logging.info(f'Подключаюсь к {device["host"]}')
        connect.enable()
        name = connect.find_prompt()
        for commanda in command:
            logging.info(f'На {device["host"]} делаю {commanda}')
            result.append(f'\n{name}{commanda}\n')
            result.append(connect.send_command(commanda))
            logging.info(f'Вывод с {device["host"]} получен')

        return result

def send_command_to_devices(devices, commands_dict, filename, limit=3):
    tasks_list = []
    result = []
    with ThreadPoolExecutor(max_workers=limit) as executor:
        for device in devices:
            command = commands_dict[device["host"]]
            task = executor.submit(send_command_func, device, command)
            tasks_list.append(task)
    with open(filename, 'w') as file:
        for task_result in tasks_list:
            result.append(task_result.result())
        for host in result:
            file.writelines(host)



if __name__ == '__main__':
    with open('devices.yaml', 'r') as file:
        reader = yaml.safe_load(file)
    send_command_to_devices(reader, commands,filename='cc.txt')'''