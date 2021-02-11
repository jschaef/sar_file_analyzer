#!/usr/bin/python3

import helpers
import sql_stuff

for record in helpers.get_metric_desc_from_manpage():
    sql_stuff.add_metric(record[0], record[1])