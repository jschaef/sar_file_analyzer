#!/usr/bin/python3
class Config(object):
    upload_dir = 'upload'
    redis_host = 'localhost'
    redis_port = 6379
    rkey_pref = 'user'
    pdf_name = 'sar_chart.pdf'
    admin_email = 'admin@example-org.com'
    max_metric_header = 8
    cols_per_line = 4
    max_header_count = 6