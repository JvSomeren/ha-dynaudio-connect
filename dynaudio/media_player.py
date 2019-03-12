"""
Support for Dynaudio Connect

Based on the API documentation found here:
https://github.com/therealmuffin/Dynaudio-connect-api
"""

import logging
import math
import socket

import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerDevice, PLATFORM_SCHEMA)
from homeassistant.components.media_player.const import (
    SUPPORT_TURN_OFF, SUPPORT_TURN_ON, SUPPORT_SELECT_SOURCE,
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_PORT, STATE_OFF, STATE_ON)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Dynaudio"
DEFAULT_PORT = 1901
DEFAULT_MAX_VOLUME = 31
DEFAULT_GREEDY_STATE = True
DEFAULT_STANDARD_ZONE = 1

SUPPORT_DYNAUDIO = SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | \
                   SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE

CONF_MAX_VOLUME = "max_volume"
CONF_GREEDY_STATE = "greedy_state"
CONF_DEFAULT_STANDARD_ZONE = "default_zone"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_MAX_VOLUME, default=DEFAULT_MAX_VOLUME): cv.positive_int,
    vol.Optional(CONF_GREEDY_STATE, default=DEFAULT_GREEDY_STATE): cv.boolean,
    vol.Optional(CONF_DEFAULT_STANDARD_ZONE, default=DEFAULT_STANDARD_ZONE): cv.positive_int
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Dynaudio platform"""
    dynaudio = DynaudioDevice(
        config.get(CONF_NAME), config.get(CONF_HOST), config.get(CONF_PORT), config.get(CONF_MAX_VOLUME), \
        config.get(CONF_GREEDY_STATE), config.get(CONF_DEFAULT_STANDARD_ZONE))
    if dynaudio.update():
        add_entities([dynaudio])


class DynaudioDevice(MediaPlayerDevice):
    """Representation of a Dynaudio device"""

    def __init__(self, name, host, port, max_volume, greedy_state, standard_zone):
        """Initialize the Dynaudio device"""
        self._name = name
        self._host = host
        self._port = port
        self._max_volume = min(max_volume, 31)
        self._greedy_state = greedy_state
        self._zone = min(standard_zone, 3)
        self._pwstate = False
        self._volume = 0
        self._muted = False
        self._selected_source = ""
        self._consecutive_connect_fails = 0
        self._fails_before_off = 3
        self._source_name_to_number = {"Minijack": 1, "Line": 2, "Optical": 3, "Coax": 4, "USB": 5, "Bluetooth": 6,
                                       "Stream": 7}
        self._source_number_to_name = {1: "Minijack", 2: "Line", 3: "Optical", 4: "Coax", 5: "USB", 6: "Bluetooth",
                                       7: "Stream"}

    @staticmethod
    def calculate_checksum(payload):
        """Calculate the checksum for the complete command"""
        hexarray = payload.split(" ")
        sum = 0
        for num in hexarray:
            sum += int(num, 16)
        x = math.ceil(sum / 255)
        checksum = x * 255 - sum - (len(hexarray) - x)
        return hex(checksum & 255)[2:]

    def construct_command(self, payload):
        """Construct full command"""
        prefix = "FF 55"
        payload_size = str(len(payload.split(" "))).zfill(2)
        checksum = self.calculate_checksum(payload)
        return prefix + " " + payload_size + " " + payload + " " + checksum

    def socket_command(self, payload):
        """Establish a socket connection and sends command"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self._host, self._port))
                hex_data = bytes.fromhex(self.construct_command(payload))
                s.send(hex_data)
                received = s.recv(1024)
                s.close()
        except ConnectionRefusedError:
            _LOGGER.warning("%s refused connection", self._name)
            return False
        except OSError:
            self._consecutive_connect_fails += 1
            if self._consecutive_connect_fails >= self._fails_before_off:
                self._pwstate = False
            return False
        self._consecutive_connect_fails = 0
        return received

    def update(self):
        """Hacky: send mute command to unused zone in order to receive feedback"""
        """Assuming only one zone is in use"""
        """Could be fixed by finding proper feedback command"""
        mute_green = "2F A0 12 00 72"
        mute_red = "2F A0 12 00 71"
        if self._zone == 1:
            payload = mute_green
        else:
            payload = mute_red
        received = self.socket_command(payload)
        if not received:
            return True
        """Update device status"""
        self._volume = float(min((int(received[7]) / self._max_volume), 1))
        self._selected_source = self._source_number_to_name[received[8]]
        self._muted = bool(received[10])
        """Below updates are hypotheses, cannot test without proper feedback command"""
        self._pwstate = bool(received[6])
        self._zone = int(received[9])
        return True

    @property
    def name(self):
        """Return the name of the device"""
        return self._name

    @property
    def state(self):
        """Return the state of the device"""
        if self._pwstate:
            return STATE_ON
        else:
            return STATE_OFF

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)"""
        return self._volume

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted"""
        return self._muted

    @property
    def supported_features(self):
        """Flag media player features that are supported"""
        return SUPPORT_DYNAUDIO

    @property
    def source(self):
        """Return the current input source"""
        return self._selected_source

    @property
    def source_list(self):
        """List of available input sources"""
        return list(self._source_name_to_number.keys())

    @property
    def media_title(self):
        """Title in Lovelace"""
        if self._pwstate:
            return self._selected_source
        else:
            return "Off"

    def turn_off(self):
        """Turn the media player off"""
        self.socket_command("2F A0 02 01 F" + str(self._zone))
        if self._greedy_state:
            self._pwstate = False

    def turn_on(self):
        """Turn the media player on"""
        self.socket_command("2F A0 01 00 F" + str(self._zone))

    def set_volume_level(self, volume):
        """Set volume level, range 0..1"""
        self.socket_command(
            "2F A0 13 " +
            str(hex(round(volume * self._max_volume))[2:]).zfill(2) +
            " 5" + str(self._zone))

    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player"""
        self.socket_command("2F A0 12 01 3" + str(self._zone))
        """Update state greedily to avoid UI delay"""
        if self._greedy_state:
            self._muted = not self._muted

    def select_source(self, source):
        """Select input source"""
        self.socket_command(
            "2F A0 15 " +
            str(self._source_name_to_number.get(source)).zfill(2) +
            " 5" + str(self._zone))
        """Update state greedily to avoid UI delay"""
        if self._greedy_state:
            self._selected_source = source
