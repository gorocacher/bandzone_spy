# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Keznikl'

import re
from BeautifulSoup import BeautifulSoup



class BandzoneFan():
    """
        Structure containing the important fan properties.
    """

    def __init__(self, nickName = None, fullName = None, avatarUrl = None, profileUrl = None, address = None):
        self.nickName = nickName
        self.fullName = fullName
        self.avatarUrl = avatarUrl
        self.profileUrl = profileUrl
        self.address = address


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

    def parseFanCount(self, html):
        """
        Parses the number of fans of a band profile (if unfolded)
        """
        soup = BeautifulSoup(html)
        result = soup.find(id="snippet-fanList-pagingControl-pagingControl")\
        .find(attrs={'class' : 'paginator'})
        return int(result["data-paginator-items"])

    def parseFans(self, html):
        """
        Parses the fan list in the left column of the page (if unfolded)
        """
        soup = BeautifulSoup(html)
        results = soup.find(id="snippet-fanList-fanList")
        links = results.findAll(attrs={'title' : re.compile(u"Přejít na profil.*")})
        items = []
        for link in links:
            fan = BandzoneFan()
            fan.profileUrl = link['href']
            fan.nickName = fan.profileUrl[5:]
            img = link.first('img', attrs={'alt' : re.compile(u"Profilový obrázek.*")})
            fan.avatarUrl = img['src']
            fullName = link.find('h4', attrs={'class' :'title'})
            fan.fullName = fullName.string
            address = link.find('span', attrs={'class' :'city'})
            fan.address = unicode(address.string)
            items.append(fan)
        return items