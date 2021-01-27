# coding: utf-8

# Copyright (c) 2019-2020 Latona. All rights reserved.

"""check-multiple-camera-connection
    check-multiple-camera-connection has roles which manage whether usb camera is attached or not and 
    tell this result via kanban or database
"""

from aion.microservice import main_decorator, Options
from aion.logger import lprint
import aion.mysql as mysql
from time import sleep
from datetime import datetime, timedelta
import subprocess

SERVICE_NAME = "check-multiple-camera-connection"
EXECUTE_INTERVAL = 1
METADATA_KEY = "device_list"


class DeviceMonitorByGstreamer:
    """DeviceMonitortByGstreamer
        Search usb deviced by v4l2-ctl command
    """
    def __init__(self):
        """
            set initial value. these command is used to get device list from host os.
            Attributes:
                cmd(str): command to get device list
                cmd_id(str): command to get serial of each usb device
        """
        self.cmd = "v4l2-ctl --list-devices"
        self.cmd_id = "ls -l /devices/v4l/by-id"

    def get_device_list(self):
        """
            get device list by v4l2-ctl command
            Returns:
                list: device list
        """
        device_list = {}
        p = subprocess.Popen(self.cmd.split(), stdout=subprocess.PIPE)
        ret = p.communicate()[0].decode()
        ret = list(filter(None, ret.split("\n")))
        for itr in range(0, len(ret), 2):
            device_list[ret[itr]] = ret[itr + 1].replace("\t", "")
        return device_list

    def get_device_list_id(self):
        """
            get device list with id. this func is developed to get a serial of a device.
            Returns:
                dict: {name: device_id}
        """
        devices = {}
        try:
            res = subprocess.check_output(self.cmd_id.split())
            by_id = res.decode()
        except Exception as e:
            print(e)
            return {}
        for line in by_id.split('\n'):
            if ('../../video' in line):
                lst = line.split(' ')
                name = ''.join(lst[-3].split('-')[1:-2])
                deviceId = lst[-1]
                deviceId = deviceId.replace('../../', '/devices/')
                devices[name] = deviceId
        return devices

class UpdateDeviceStateToDB(mysql.BaseMysqlAccess):
    """UpdateDeviceStateToDB
        Store device list to mysql
        This function will be deleted. 
    """
    def __init__(self):
        super().__init__("PeripheralDevice")

    def update_up_device_state(self, serial, path):
        """
            update device state in mysql
            Args:
                serial(str): a serial number of a device
                path(str): device path
        """
        sql = """
            INSERT INTO cameras(serial, path, state)
                VALUES (%(serial)s,%(path)s, %(state)s)
            ON DUPLICATE KEY UPDATE
                path = IF(path = %(path)s, path, values(path)),
                state = IF(state = %(state)s, state, values(state)),
                timestamp = CURRENT_TIMESTAMP()
            """
        args = {"serial": serial, "path": path, "state": 1}
        self.set_query(sql, args)

    def update_down_device_state(self):
        """
            update device state in mysql which is not attached
        """
        now = datetime.now() - timedelta(seconds=1)
        sql = """
            UPDATE cameras
            SET path = "", state = 0
            WHERE timestamp < %(time)s
            """
        args = {"time": now.strftime('%Y-%m-%d %H:%M:%S')}
        self.set_query(sql, args)

    def check_invalid_state(self):
        """
            update device state in mysql which is not attached
        """
        now = datetime.now() + timedelta(seconds=10)
        sql = """
            UPDATE cameras
            SET path = "", state = 0
            WHERE timestamp > %(time)s
            """
        args = {"time": now.strftime('%Y-%m-%d %H:%M:%S')}
        self.set_query(sql, args)


@main_decorator(SERVICE_NAME)
def main(opt: Options):
    conn = opt.get_conn()
    num = opt.get_number()
    # get cache kanban
    kanban = conn.set_kanban(SERVICE_NAME, num)

    dm = DeviceMonitorByGstreamer()
    metadata = {METADATA_KEY: {}}
    while True:
        device_list = dm.get_device_list_id()
        if metadata[METADATA_KEY] != device_list:
            lprint("change device status: ", device_list)
            metadata = {METADATA_KEY: device_list}
            for serial, device_id in device_list.items():
                # output after kanban
                conn.output_kanban(
                    connection_key=device_id.split('/')[-1],
                    metadata={METADATA_KEY: {serial: device_id}},
                )
        sleep(EXECUTE_INTERVAL)
        try: 
            with UpdateDeviceStateToDB() as my:
                # devices = list(device_list.keys())
                for device_id, path in device_list.items():
                    my.update_up_device_state(device_id, path)
                my.update_down_device_state()
                my.check_invalid_state()
                my.commit_query()
                lprint("finish to update camera state")
        except Exception as e:
            lprint(str(e))
