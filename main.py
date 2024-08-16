#  -*- coding: utf-8 -*-
"""
dashcal: comic dash calender to ical

Rresponse ical data from ComicDash! new comic calender
    http GET method
        /ical ... Convert to ical data
"""
import logging
import re
import traceback
from datetime import datetime
from datetime import timedelta

import requests
import pytz
from flask import Flask, request, make_response
from google.cloud import datastore

from dashcal import DashCal

app = Flask(__name__)
client = datastore.Client()
japan_time = pytz.timezone('Asia/Tokyo')


@app.route('/ical')
def convert():
    """Convert to ical data"""
    def get_user():
        """get username from GET parameter"""
        username = request.args.get("user", "")
        if username:
            user = re.match(r'(^[A-Za-z][A-Za-z0-9-]+$)', username)
        else:
            user = None
        if user:
            return user.group(1)
        raise ValueError

    def get_from_cache(user, limit):
        """get html from cache"""
        logging.info('get_from_cahce')
        key = client.key('Cache', user)
        entity = client.get(key)
        if entity is not None:
            if entity.dt > limit:
                return entity.html
        return None

    def put_to_cache(user, html):
        """put html to cache"""
        key = client.key('Cache', user)
        entity = datastore.Entity(key=key)
        entity["dt"] = datetime.now(japan_time)
        entity["html"] = html
        client.put(entity)

    def fetch_from_site(user):
        logging.info('fetch_from_site')
        url = "https://ckworks.jp/comicdash/calendar/" + user
        try:
            res = requests.get(url, timeout=60.0)
        except requests.Timeout:
            logging.error('request timeout, user: %s', user)
            return None
        except Exception as err:
            logging.error('Unexpected %s, %s', err, type(err))
            logging.error(traceback.format_exc())
            raise
        # Convert to ical data
        logging.info('res.content: %s', res.content[0:20])
        if (res.content is None or res.content == b'\n'):
            return None
        put_to_cache(user, res.content)
        return res.content

    # get user
    try:
        user = get_user()
    except ValueError:
        # invalid user
        resp = make_response("", 400)
        logging.info('invalid user')
        return resp

    # get from cache
    limit = datetime.now(japan_time) - timedelta(days=1)
    html = get_from_cache(user, limit)

    # fetch from site
    if html is None:
        html = fetch_from_site(user)

    # return error response
    if html is None:
        logging.error('response is null')
        resp = make_response("", 500)
        return resp

    dashcal = DashCal(html)
    ical = dashcal.to_ical()
    status = 200
    headers = {}
    headers["Content-Type"] = "text/plain;charset=UTF-8"
    resp = make_response((ical, status, headers))
    return resp


logging.getLogger().setLevel(logging.INFO)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
