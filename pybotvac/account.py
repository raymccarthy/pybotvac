"""Account access and data handling for beehive endpoint."""

import binascii
import os
import shutil
import requests

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from .robot import Robot


class Account:
    """
    Class with data and methods for interacting with a pybotvac cloud session.

    :param email: Email for pybotvac account
    :param password: Password for pybotvac account

    """

    ENDPOINT = 'https://beehive.neatocloud.com/'

    def __init__(self, email, password):
        """Initialize the account data."""
        self._robots = set()
        self.robot_serials = {}
        self._maps = {}
        self._headers = {'Accept': 'application/vnd.neato.nucleo.v1'}
        self._login(email, password)

    def _login(self, email, password):
        """
        Login to pybotvac account using provided email and password.

        :param email: email for pybotvac account
        :param password: Password for pybotvac account
        :return:
        """
        response = requests.post(urljoin(self.ENDPOINT, 'sessions'),
                             json={'email': email,
                                   'password': password,
                                   'platform': 'ios',
                                   'token': binascii.hexlify(os.urandom(64)).decode('utf8')},
                             headers=self._headers)

        response.raise_for_status()
        access_token = response.json()['access_token']

        self._headers['Authorization'] = 'Token token=%s' % access_token

    @property
    def robots(self):
        """
        Return set of robots for logged in account.

        :return:
        """
        if not self._robots:
            self.refresh_robots()

        return self._robots

    @property
    def maps(self):
        """
        Return set of userdata for logged in account.

        :return:
        """
        if not self._maps:
            self.refresh_robots()

        return self._maps

    def refresh_robots(self):
        """
        Get information about robots connected to account.

        :return:
        """
        resp = requests.get(urljoin(self.ENDPOINT, 'dashboard'),
                            headers=self._headers)
        resp.raise_for_status()

        for robot in resp.json()['robots']:
            self._robots.add(Robot(name=robot['name'],
                                   serial=robot['serial'],
                                   secret=robot['secret_key'],
                                   traits=robot['traits']))
            resp2 = (
                requests.get(urljoin(self.ENDPOINT,
                                     'users/me/robots/{0}/maps'.format(robot['serial'])),
                             headers=self._headers))
            resp2.raise_for_status()
            self._maps.update = ({robot['serial']: resp2.json()})

    @staticmethod
    def get_map_image(url, dest_path):
        """
        Return a requested map from a robot.

        :return:
        """
        image_url = url.rsplit('/', 2)[1] + '-' + url.rsplit('/', 1)[1]
        image_filename = image_url.split('?')[0]
        dest = os.path.join(dest_path, image_filename)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest, 'wb') as data:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, data)
