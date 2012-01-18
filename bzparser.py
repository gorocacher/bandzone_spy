# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Keznikl'

import re
from BeautifulSoup import BeautifulSoup



class BandzoneFan():
    """
        Structure containing the important fan properties.
    """

    def __init__(self):
        self.nickName = None
        self.fullName = None
        self.avatarUrl = None
        self.profileUrl = None
        self.city = None


class BandzoneBandParser():
    """
    Parses the bandzone band profile page.
    """

    def parseFanPageCount(self, html):
        """
        Parses the number of pages showing the fans of a band profile (if unfolded)
        """
        soup = BeautifulSoup(html)
        result = soup.find(id="snippet-fanList-pagingControl-pagingControl")\
            .find(attrs={'class' : 'paginator'})
        return int(result["data-paginator-pages"])

    def parseFans(self, html):
        """
        Parses the fan list in the left column of the page (if unfolded)
        """
        soup = BeautifulSoup(html)
        results = soup.find(id="snippet-fanList-fanList")
        links = results.findAll(attrs={'title' : re.compile(u"Přejít na profil.*")})
        items = []
        for link in links:
            item = link['href']
            items.append(item)
        return items