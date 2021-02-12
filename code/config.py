#!/usr/bin/python3

class Config(object):
    upload_dir = 'upload'
    colors = {'green': '#29910E',
              'blue': '#004c97',
              'red': '#FF0000',
              'ligth_green': '#98FB98',
              'light_blue': '#b2c1d3',
              'ligth_red': '#FFA07A',
              'gold': '#FFD700',
              'brown': '#8B4513'}
    redis_host = 'localhost'
    redis_port = 6379
    rkey_pref = 'user'
    pdf_name = 'sar_chart.pdf'
    admin_email = 'jochen.schaefer@suse.com'

