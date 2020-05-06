#
# Python GWS base setting
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import os

# app settings
app_host        = 'localhost'
app_port        = 3000
app_protocol    = 'http'  # http | ws
app_dir         = os.path.dirname(os.path.abspath(__file__))
static_path     = os.path.join(app_dir, 'static')

# database settings
db_path         = os.path.join(app_dir,'../db.sqlite3')    # ':memory:'

# test
is_test         = False





