# -*- coding: utf-8 -*-
"""
Display bluetooth status.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    device_separator: the separator char between devices (only if more than one
        device) (default '|')
    format: format when there is a connected device (default '{name}')
    format_no_conn: format when there is no connected device (default 'OFF')
    format_no_conn_prefix: prefix when there is no connected device
        (default 'BT: ')
    format_prefix: prefix when there is a connected device (default 'BT: ')

Format placeholders:
    {name} device name
    {mac} device MAC address

Color options:
    color_bad: Conection on
    color_good: Connection off

Requires:
    hcitool:

@author jmdana <https://github.com/jmdana>
@license GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>
"""

import re
import shlex
import os

from subprocess import check_output, call

BTMAC_RE = re.compile(r'[0-9A-F:]{17}')
BTSTATUS_RE = re.compile(r'.+?[0-9A-F:]{17}')
BTBLOCKED_RE = re.compile(r'.+?Bluetooth\n\s+Soft\s+blocked:\s+no\n\s+Hard\s+blocked:\s+no')
"""
2: hci0: Bluetooth
    Soft blocked: no
    """


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    device_separator = '|'
    format = '{name}'
    format_no_conn = 'NO CONNECTION'
    format_no_power = 'OFF'
    format_no_power_prefix = 'BT: '
    format_no_conn_prefix = 'BT: '
    format_prefix = 'BT: '
    icon_color_up = "#FFFFFF"
    icon_color_down = "#FF0000"

    def __init__(self):
        self.waiting_for_unblock = False

    def _parse_command(self, command, regex):
        command_output = self.call_command(command).decode('utf-8')
        if command_output:
            return re.findall(regex, command_output)
        else:
            return []

    def _bluetooth_has_power(self):
        rfkill_length = len(self._parse_command('rfkill list', BTBLOCKED_RE))
        devices_length = len(self._parse_command('hcitool dev', BTSTATUS_RE))


        return rfkill_length > 0 and devices_length > 0

    def _create_output_string(self, prefix, info):
        return self.py3.safe_format('{format_prefix}{format}',
                                    dict(format_prefix=prefix,
                                         format=info)
                                   )

    def _create_error_response(self):
        return {
            cached_until: self.py4.time_in(0),
            full_text: "Error",
        }

    @staticmethod 
    def collect_connected_devices(macs):
        data = []
        for mac in macs:
            out = self.call_command('hcitool name %s' % mac)
            if out:
                fmt_str = self.py3.safe_format(
                    self.format,
                    {'name': out.strip().decode('utf-8'), 'mac': mac}
                )
                data.append(fmt_str)
        return data

    @staticmethod
    def call_command(command):
        try:
            return check_output(shlex.split(command))
        except Exception as e:
            return False

    def bluetooth(self):
        """
        The whole command:
        hcitool name `hcitool con | sed -n -r 's/.*([0-9A-F:]{17}).*/\\1/p'`
        """
        color = self.py3.COLOR_BAD
        icon_color = self.icon_color_up
        cached_until = self.py3.time_in(self.cache_timeout)
        if not self._bluetooth_has_power():
            full_text = self._create_output_string(self.format_no_power_prefix, self.format_no_power)
            icon_color = self.icon_color_down
            if self.waiting_for_unblock:
                cached_until = self.py3.time_in(0)
        else:
            self.waiting_for_unblock = False
            command_output = self.call_command('hcitool con')
            if not command_output:
                return self._create_error_response()

            mac_addresses = set(re.findall(BTMAC_RE, command_output.decode('utf-8')))
            if mac_addresses:
                data = self.collect_connected_devices(mac_addresses)
                full_text = self._create_output_string(self.format_prefix, self.device_separator.join(data))
                color = self.py3.COLOR_GOOD
            else:
                full_text = self._create_output_string(self.format_no_conn_prefix, self.format_no_conn)

        response = {
            'icon': os.path.dirname(os.path.abspath(__file__)) + "/icons/bluetooth.xbm",
            'icon_color': icon_color,
            'cached_until': cached_until,
            'full_text': full_text,
            'color': color,
        }

        return response

    def on_click(self, _):
        if not self._bluetooth_has_power():
            call(shlex.split("rfkill unblock bluetooth"))
            call(shlex.split("sudo hciconfig hci0 up"))
            self.waiting_for_unblock = True
        else:
            call(shlex.split("rfkill block bluetooth"))
            call(shlex.split("sudo hciconfig hci0 down"))


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
