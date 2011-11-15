#  -*- coding: utf-8 -*-
"""
dashcal: comic dash calender to ical

Rresponse ical data from ComicDash! new comic calender
    http GET method
        /ical ... Convert to ical data
"""
import logging
import re
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from dashcal import DashCal


class Converter(webapp.RequestHandler):
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
        # fetch
        url = "http://ckworks.jp/comicdash/calendar/" + user
        page = urlfetch.fetch(url)
        # Convert to ical data
        if page.status_code == 200:
            dashcal = DashCal(page.content)
            self.response.out.write(dashcal.to_ical())


logging.getLogger().setLevel(logging.DEBUG)
APPLICATION = webapp.WSGIApplication(
    [("/ical", Converter)], debug=True)


def real_main():
    """run application"""
    run_wsgi_app(APPLICATION)


def profile_main():
    """get profile"""
    # This is the main function for profiling
    # We've renamed our original main() above to real_main()
    #prof = cProfile.Profile()
    #prof = prof.runctx("real_main()", globals(), locals())
    #stream = StringIO.StringIO()
    #stats = pstats.Stats(prof, stream=stream)
    #stats.sort_stats("time")  # Or cumulative
    #stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    #logging.info("Profile data:\n%s", stream.getvalue())


if __name__ == "__main__":
    real_main()
