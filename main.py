#  -*- coding: utf-8 -*-
"""
dashcal: comic dash calender to ical

Rresponse ical data from ComicDash! new comic calender
    http GET method
        /ical ... Convert to ical data
"""
import logging
import re
import webapp2
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from dashcal import DashCal


class Converter(webapp2.RequestHandler):
    """Convertier class"""
    def get(self):
        """Convert to ical data"""
        def get_user():
            """get username from GET parameter"""
            username = self.request.get("user")
            if username:
                user = re.match(r'(^[A-Za-z][A-Za-z0-9-]+$)', username)
            else:
                user = None
            if user:
                return user.group(1)
            else:
                raise ValueError

        # Set Content-Type
        self.response.headers["Content-Type"] = "text/plain;charset=UTF-8"
        # get user
        try:
            user = get_user()
        except ValueError:
            # invalid user
            self.response.set_status(400)
            return
        page = memcache.get(user)
        if page is not None:
            dashcal = DashCal(page.content)
            self.response.out.write(dashcal.to_ical())
            return
        # fetch
        url = "http://ckworks.jp/comicdash/calendar/" + user
        page = urlfetch.fetch(url, deadline=10)
        # Convert to ical data
        if page.status_code == 200:
            memcache.add(user, page, time=7200)
            dashcal = DashCal(page.content)
            self.response.out.write(dashcal.to_ical())


logging.getLogger().setLevel(logging.INFO)
app = webapp2.WSGIApplication(
    [("/ical", Converter)], debug=True)
