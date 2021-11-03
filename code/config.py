#!/usr/bin/python3
from tzlocal import get_localzone
class Config(object):
    local_tz = get_localzone()
    upload_dir = 'upload'
    redis_host = 'localhost'
    redis_port = 6379
    rkey_pref = 'user'
    pdf_name = 'sar_chart.pdf'
    admin_email = 'admin@example-org.com'
    timezone = local_tz.zone

