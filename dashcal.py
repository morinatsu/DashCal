#  -*- coding: utf-8 -*-
"""
dashcal: comic dash calendar to ical

    convert ComicDash! new comic calendar to .ical
"""
import re
import logging
from bs4 import BeautifulSoup
logging.getLogger().setLevel(logging.DEBUG)


class DashCal(object):
    """converter class http responce to ical"""
    def __init__(self, html):
        """initialize instance"""
        def pickup_entry(entry):
            """pickup information from entry

            Pickup title, cover image and publish date of books
            from entry of ComicDash calender.

            Args:
                A book entry(div node) of 'listedit' form

            Returns:
                A dict of information of book

                {'date': publish date of book,
                 'title': title of book,
                 'image': cover image of book}

            """
            matched_title = re.search(
                r'<a href="/comicdash/series/[0-9]+">([^<>]*)</a><br',
                unicode(entry),
                re.M
                )
            if matched_title:
                title = matched_title.group(1)
                logging.debug('title: %s', unicode(title)[0:50])
            else:
                title = None
            matched_image = re.search(
                r'<img.*/>',
                unicode(entry),
                re.M
                )
            if matched_image:
                image = matched_image.group(0)
                logging.debug('image: %s', unicode(image)[0:50])
            else:
                image = None
            matched_date = re.search(
                r'([0-9]{4}/[0-9]{2}/[0-9]{2})',
                unicode(entry),
                re.M
                )
            if matched_date:
                date = matched_date.group(1)
                logging.debug('date: %s', unicode(date)[0:50])
            else:
                date = None
            return dict({"date": date, "title": title, "image": image})

        self.html = html
        self.booklist = []
        soup = BeautifulSoup(html)
        main_content = soup.body.find('div', id='main')
        logging.debug('main_content: %s', unicode(main_content)[0:20])
        listedit = main_content.find(
            'form',
            attrs={'name': 'listedit'}
            )
        logging.debug('listedit: %s', unicode(listedit)[0:20])
        entries = listedit.find_all('div', recursive=False)
        for entry in entries:
            logging.debug('entry: %s', unicode(entry)[0:50])
            self.booklist.append(pickup_entry(entry))

    def to_ical(self):
        """convert to ical data"""
        def to_ical_entry(book):
            """book information convert to ical format

            Generate ical data from information of book

            Args:
                item of self.booklist

            Returns:
                list of string(a VEVENT)
            """
            date = book['date'].replace("/", "")
            return [u"BEGIN:VEVENT",
                    u"DTSTART;VALUE=DATE:%(dtstart)s" % {'dtstart': date},
                    u"DTEND;VALUE=DATE:%(dtend)s" % {'dtend': date},
                    u"SUMMARY:%(title)s" % {'title': book['title']},
                    u"DESCRIPTION;ENCODING=QUOTED-PRINTABLE:No description",
                    u"END:VEVENT"
                   ]

        # header
        ical = [u"BEGIN:VCALENDAR",
                u"PRODID:DashCal",
                u"X-WR-CALNAME:ComicDashCalender",
                u"VERSION:2.0"]
        # vevents
        for book in self.booklist:
            if book['date']:
                ical.extend(to_ical_entry(book))
        # footer
        ical.append(u"END:VCALENDAR")
        return "\n".join(ical)


if __name__ == "__main__":
    html = open('morinatsu.html', 'r')
    dashcal = DashCal(html)
    print dashcal.to_ical()
