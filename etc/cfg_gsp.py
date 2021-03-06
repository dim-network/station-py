# -*- coding: utf-8 -*-

"""
    Genesis Service Providers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Configuration of stations
"""

import os

etc = os.path.abspath(os.path.dirname(__file__))

#
# Current Station
#

# station_id = 'gsp-s001@x5Zh9ixt8ECr59XLye1y5WWfaX4fcoaaSC'
station_id = 'gsp-s002@wpjUWg1oYDnkHh74tHQFPxii6q9j3ymnyW'

station_name = 'Genesis Station (GZ)'
station_host = '0.0.0.0'
station_port = 9394

#
#  All Station List
#
all_stations = [
    'gsp-s001@x5Zh9ixt8ECr59XLye1y5WWfaX4fcoaaSC',
    'gsp-s002@wpjUWg1oYDnkHh74tHQFPxii6q9j3ymnyW',
]


#
#  Local Station List
#
local_servers = [
    'gsp-s001@x5Zh9ixt8ECr59XLye1y5WWfaX4fcoaaSC',
    'gsp-s002@wpjUWg1oYDnkHh74tHQFPxii6q9j3ymnyW',
]
