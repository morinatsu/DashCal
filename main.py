#  -*- coding: utf-8 -*-
"""
dashcal: comic dash calender to ical

Rresponse ical data from ComicDash! new comic calender
    http GET method
        /ical ... Convert to ical data
"""
import logging
import re
import requests
from flask import Flask, request, make_response
from dashcal import DashCal

app = Flask(__name__)


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

    # get user
    try:
        user = get_user()
    except ValueError:
        # invalid user
        resp = make_response("", 400)
        return resp
    # fetch
    url = "http://ckworks.jp/comicdash/calendar/" + user
    try:
        res = requests.get(url, timeout=60.0)
    except requests.Timeout:
        resp = make_response("", 500)
        return resp
    # Convert to ical data
    dashcal = DashCal(res.content)
    ical = dashcal.to_ical()
    status = 200
    headers = {}
    headers["Content-Type"] = "text/plain;charset=UTF-8"
    resp = make_response((ical, status, headers))
    return resp


logging.getLogger().setLevel(logging.INFO)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
