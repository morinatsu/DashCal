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
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch_errors
from dashcal import DashCal


class Converter(webapp2.RequestHandler):
    """Converter class"""
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
        page_content = memcache.get(user)
        if page_content is None:
            # fetch
            url = "http://ckworks.jp/comicdash/calendar/" + user
            try:
                page = urlfetch.fetch(url, deadline=10)
            except urlfetch_errors.DeadlineExceededError:
                taskqueue.add(url='/fetcher', params={'user': user})
                self.response.set_status(500)
                return
            if page.status_code == 200:
                page_content = page.content
                memcache.add(user, page_content, time=7200)
        # Convert to ical data
        dashcal = DashCal(page_content)
        self.response.out.write(dashcal.to_ical())


class Fetcher(webapp2.RequestHandler):
    """Fetcher class"""
    def post(self):
        """Cache page content offline"""
        user = self.request.get("user")
        page_content = memcache.get(user)
        if page_content is not None:
            return
        # fetch
        url = "http://ckworks.jp/comicdash/calendar/" + user
        page = urlfetch.fetch(url, deadline=120)
        # Cache page content
        if page.status_code == 200:
            memcache.add(user, page.content, time=7200)


logging.getLogger().setLevel(logging.INFO)
app = webapp2.WSGIApplication(
    [("/ical", Converter),
     ("/fetcher", Fetcher)], debug=True)
