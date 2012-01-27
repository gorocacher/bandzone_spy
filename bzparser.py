# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Methods and classes for parsing a given band-profile HTML.
Uses the BeautifulSoup parsing library.
"""

__author__ = 'Keznikl'

import re
from BeautifulSoup import BeautifulSoup

class BandzoneFan():
    """Structure containing the important fan properties.

    Attributes:
        nickName (str): Nick name of the fan.
        fullName(str): Full profile name of the fan.
        avatarURL (str): Absolute URL of the fan's avatar (starting http://).
        profileURL (str): Relative URL of the fan's profile (starting /).
        address (str): Address of the fan.
    """
    def __init__(self, nickName = None, fullName = None, avatarUrl = None, profileUrl = None, address = None):
        self.nickName = nickName
        self.fullName = fullName
        self.avatarUrl = avatarUrl
        self.profileUrl = profileUrl
        self.address = address


def parseFanPageCount(html):
    """Parses the number of pages containing the fans of a given band profile.

    The  fan list in the band profile is expected to be unfolded in the given html.

    Args:
        html (str): The HTML page to be parsed.

    Returns (int):
        The nuber of fan-list pages.

    Raises:
        TODO various errors when the given html cannot be parsed.
    """
    soup = BeautifulSoup(html)
    result = soup.find(id="snippet-fanList-pagingControl-pagingControl")\
        .find(attrs={'class' : 'paginator'})
    return int(result["data-paginator-pages"])

def parseFanCount(html):
    """Parses the number of fans of a band profile.

    The  fan list in the band profile is expected to be unfolded in the given html.

    Args:
        html (str): The HTML page to be parsed.

    Returns (int):
        The number of fans of the band.

    Raises:
        TODO various errors when the given html cannot be parsed.
    """
    soup = BeautifulSoup(html)
    result = soup.find(id="snippet-fanList-pagingControl-pagingControl")\
    .find(attrs={'class' : 'paginator'})
    return int(result["data-paginator-items"])

def parseFans(html):
    """
    Parses the fans listed on the bands profile.

    The  fan list in the band profile is expected to be unfolded in the given html.

    Args:
        html (str): The HTML page to be parsed.

    Returns (list[BandzoneFan]):
    The list of fans listed on the band profile.

    Raises:
    TODO various errors when the given html cannot be parsed.
    """
    try:
        soup = BeautifulSoup(html)
        results = soup.find(id="snippet-fanList-fanList")
        links = results.findAll(attrs={'title' : re.compile(u"Přejít na profil.*")})
        items = []
        for link in links:
           fan = BandzoneFan()
           fan.profileUrl = unicode(link['href'])
           fan.nickName = unicode(fan.profileUrl[5:])
           img = link.first('img', attrs={'alt' : re.compile(u"Profilový obrázek.*")})
           fan.avatarUrl = unicode(img['src'])
           fullName = link.find('h4', attrs={'class' :'title'})
           fan.fullName = unicode(fullName.string)
           address = link.find('span', attrs={'class' :'city'})
           fan.address = unicode(address.string)
           items.append(fan)
        return items
    except:
        return []