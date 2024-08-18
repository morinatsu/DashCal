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
import os
from datetime import datetime
from datetime import timedelta

import requests
import pytz
from flask import Flask, request, make_response
from google.cloud import storage

from dashcal import DashCal

app = Flask(__name__)
client = storage.Client()
bucket_name = os.environ["BUCKET_NAME"]
japan_time = pytz.timezone('Asia/Tokyo')


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
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(user)
    if blob.exists() is True:
        blob.reload()
        logging.debug('cache.created: %s, limit: %s',
                      blob.time_created,
                      limit)
        if (blob.time_created is None) or \
           (blob.time_created > limit):
            return blob.download_as_text()
    return None


def put_to_cache(user, html):
    """put html to cache"""
    logging.info('put_to_cahce')
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(user)
    blob.upload_from_string(html)


def fetch_from_site(user):
    """fetch html from comic-dash website"""
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


@app.route('/ical')
def convert():
    """Convert to ical data"""

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
