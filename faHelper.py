# -*- coding: utf-8 -*-

import re
import sys

import cookielib
import urllib
import urllib2
from bs4 import BeautifulSoup

import common


# From October 12, 2015 to 20151012
def changeDateString(dateBad):
    date = dateBad.split(" ")
    date[0] = date[0].replace("January", "01")
    date[0] = date[0].replace("February", "02")
    date[0] = date[0].replace("March", "03")
    date[0] = date[0].replace("April", "04")
    date[0] = date[0].replace("May", "05")
    date[0] = date[0].replace("June", "06")
    date[0] = date[0].replace("July", "07")
    date[0] = date[0].replace("August", "08")
    date[0] = date[0].replace("September", "09")
    date[0] = date[0].replace("October", "10")
    date[0] = date[0].replace("November", "11")
    date[0] = date[0].replace("December", "12")
    date[1] = date[1].replace(",", "")

    if len(date[1]) == 1:
        date[1] = "0" + date[1]

    dateGood = date[2] + date[0] + date[1]
    return dateGood


class FAhelper:
    """Clase para ayudar a bajar la informacion de filmaffinity"""

    # FA URL set.
    # urlLogin= "http://www.filmaffinity.com/en/login.php"
    urlLogin = "https://filmaffinity.com/en/account.ajax.php?action=login"  # New login URL? seems it works
    urlVotes = "http://www.filmaffinity.com/en/myvotes.php"
    urlVotes_prefix = "http://www.filmaffinity.com/en/myvotes.php?p="
    urlVotes_sufix = "&orderby="
    urlVotesID = "http://www.filmaffinity.com/en/userratings.php?user_id="
    urlVotesIDpageSufix = "&p="

    urlFilm = "http://www.filmaffinity.com/en/film"
    urlFilmSufix = ".html"

    urlMain = "http://www.filmaffinity.com/en/main.php"

    def __init__(self):
        self.userId = "0"

        # Enable cookie support for urllib2
        self.__cookiejar = cookielib.CookieJar()
        self.__webSession = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.__cookiejar))

        self.__faMovies = []
        self.__faMoviesFilled = []

    def setUserID(self, userId):
        self.userId = str(userId)

    def login(self, user, password):
        self.__userName = user
        self.__userPass = password

        self.__webSession.open(self.urlLogin)

        # Post data to Filmaffinity login URL.
        dataForm = {"postback": 1, "rp": "", "username": user,
                    "password": password}  # a 30/10/2015 Han cambiado el formulario de login, que alegria
        dataPost = urllib.urlencode(dataForm)
        request = urllib2.Request(self.urlLogin, dataPost)
        self.__webSession.open(request)  # Our cookiejar automatically receives the cookies, after the request

        webResponse = self.__webSession.open(self.urlVotes)
        pattern = re.compile('\?user_id=(\d+)"')
        match = pattern.search(webResponse.read())

        if match:
            userID = match.group(1)
        else:
            raise NotImplementedError(
                "ERROR FOUND: change regular expression at login() for user ID. Probably FA changed web page structure")

        self.userId = userID

    # returns 1 when login is succeed
    def loginSucceed(self):
        return len(self.__cookiejar) > 1

    # returns value of film affinity user ID
    def getUserID(self):
        return self.userId

    def getNumVotes(self):

        if self.userId == "0":
            raise Exception("ERROR FOUND: No user id found. Please login or set user id.")

        url = self.urlVotesID + self.userId
        webResponse = self.__webSession.open(url)
        html = webResponse.read()
        pattern = re.compile('Page <b>1<\/b> of <b>([\d]+)<\/b>')
        match = pattern.search(html)
        if not match:
            raise NotImplementedError(
                "ERROR FOUND: change regular expression at getNumVotes() for numPages. Probably FA changed web page structure")

        numPages = match.group(1)

        pattern = re.compile('<div class="number">([\d,\.]+)<\/div>[\r\n\s\t]+<div class="text">Votes<\/div>')
        match = pattern.search(html)
        if not match:
            raise NotImplementedError(
                "Change regular expression at getVotesByID() for numVotes. Probably FA changed web page structure")

        numVotes = match.group(1)

        return numVotes, numPages

    class FAMovieData:

        def __init__(self, movieID, movieTitle, movieYear, movieRate, dayYYYYMMDD):
            self.movieID = movieID
            self.movieTitle = movieTitle
            self.movieYear = movieYear
            self.movieRate = movieRate
            self.dayYYYYMMDD = dayYYYYMMDD

        def get_id(self):
            return self.movieID

        def get_title(self):
            return self.movieTitle

        def get_year(self):
            return self.movieYear

        def get_rate(self):
            return self.movieRate

        def set_extra_info(self, ei):
            self.extra_info = ei

        report_attr_names = ("ID", "Title", "Year", "Vote", "Voted", "Country", "Director", "Cast", "Genre", 'url')

        def report_attr_values(self):
            return self.get_id(), self.get_title(), self.get_year(), self.movieRate, None, self.extra_info.movieCountry, self.extra_info.movieDirector, self.extra_info.movieCast, self.extra_info.movieGenre, self.extra_info.url

    def getDumpVotesPage(self, page):

        if self.userId == "0":
            raise Exception("ERROR FOUND: No user id found. Please login or set user id.")

        url = self.urlVotesID + str(self.userId) + self.urlVotesIDpageSufix + str(page)
        webResponse = self.__webSession.open(url)
        html = webResponse.read()
        html = unicode(html, 'utf-8')

        soupPage = BeautifulSoup(html, 'html.parser')
        daysDiv = soupPage.body.findAll('div', attrs={'class': 'user-ratings-wrapper'})
        for dayDiv in daysDiv:

            # Get day when the vote was done:
            day = dayDiv.find('div', attrs={'class': 'user-ratings-header'})
            dayBadFormat = day.text.replace("Rated on ", "")
            dayYYYYMMDD = changeDateString(dayBadFormat)

            # Each day may have more than one movie:
            rates = dayDiv.findAll('div', attrs={'class': 'user-ratings-movie fa-shadow'})
            for movie in rates:

                # Get filmaffinity ID
                movieID = movie.find('div', attrs={'class': 'movie-card movie-card-0'}).get("data-movie-id")

                # Get movie rate
                movieRate = movie.find('div', attrs={'class': 'ur-mr-rat'}).text

                # Get title
                title = movie.find('div', attrs={'class': 'mc-title'})

                pattern = re.compile('\((\d\d\d\d)\)')
                match = pattern.search(title.text)
                if not match:
                    raise NotImplementedError(
                        "ERROR FOUND: change regular expression at getDumpVotesPage() for movie year. Probably FA changed web page structure")

                movieYear = match.group(1)
                movieTitle = title.text.replace("(" + movieYear + ")", "").strip()
                movieTitle = movieTitle.replace("(TV Series)", "").strip()
                movieTitle = movieTitle.replace("(TV)", "").strip()
                movieTitle = movieTitle.replace("(S)", "").strip()

                movieResult = self.FAMovieData(movieID=movieID, movieTitle=movieTitle, movieYear=movieYear,
                                               movieRate=movieRate, dayYYYYMMDD=dayYYYYMMDD)
                # print movieID, movieTitle, movieYear, movieRate, dayYYYYMMDD
                self.__faMovies.append(movieResult)

    class FaMovieExtraInfo:

        def __init__(self, movieTitle, movieYear, movieCountry, movieDirector, movieCast, movieGenre, url):
            self.movieTitle = movieTitle
            self.movieYear = movieYear
            self.movieCountry = movieCountry
            self.movieDirector = movieDirector
            self.movieCast = movieCast
            self.movieGenre = movieGenre
            self.url = url

    def getMovieUrl(self, movieID):
        return self.urlFilm + str(movieID) + self.urlFilmSufix

    def getMovieInfoById(self, movieID):

        found = 0
        intento = 0
        url = self.getMovieUrl(movieID)
        while found == 0:
            if intento < 3:
                webResponse = self.__webSession.open(url)

                html = webResponse.read()

                from bs4 import BeautifulSoup
                soupPage = BeautifulSoup(html, 'html.parser')

                html = unicode(html, 'utf-8')
                if webResponse.getcode() != 200:
                    print(webResponse.getcode())

                # Get movie title information
                pattern = re.compile('<span itemprop="name">([\w\W\s]+?)<\/span>')
                match = pattern.search(html)
                if match:
                    movieTitle = match.group(1)
                    movieTitle = movieTitle.replace("(TV Series)", "").strip()
                    movieTitle = movieTitle.replace("(TV)", "").strip()
                    movieTitle = movieTitle.replace("(S)", "").strip()

                    found = 1
                else:
                    intento = intento + 1
            else:
                raise NotImplementedError(
                    "ERROR FOUND: change regular expression at getMovieInfoById() for movie title. Probably FA changed web page structure. Movie ID: " + str(
                        movieID))

        # Get movie year information
        pattern = re.compile('<dt>Year<\/dt>[\s\r\n]+<dd[\w\W]+?>(\d\d\d\d)<\/dd>')
        match = pattern.search(html)
        if not match:
            raise NotImplementedError(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie year. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))
        movieYear = match.group(1)

        # Get movie country information
        country_img_tag = soupPage.body.find(id='country-img')
        country_text = country_img_tag.next_sibling
        movieCountry = country_text.strip()
        if movieCountry is None or len(movieCountry) < 2:
            raise NotImplementedError(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie county. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))

        # Get movie director information
        pattern = re.compile('<dt>Director<\/dt>[\w\s\W\r\n]+?<span itemprop="name">([\w\W\s]+?)<\/span>')
        match = pattern.search(html)
        if match:
            movieDirector = match.group(1)
            movieDirector = movieDirector.strip()
        else:
            raise NotImplementedError(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie director. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))

        # Get movie cast information
        pattern = re.compile('<dt>Cast<\/dt>[\s\r\n]+?<dd>([\w\W]+?)<\/dd>')
        match = pattern.search(html)
        if match:
            castWithLink = match.group(1)
            castWithLink = re.sub('\s?<a href=[\w\W]+?>', "", castWithLink)
            movieCast = castWithLink.replace("</a>", "")
            movieCast = movieCast.replace("\r\n", " ")
            movieCast = movieCast.strip()
        else:
            print(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie cast. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))
            movieCast = "None"

        # Get movie genre infomration
        pattern = re.compile('<dt>Genre<\/dt>[\s\r\n]+?<dd>([\w\W]+?)<\/dd>')
        match = pattern.search(html)
        if match:
            genreWithLink = match.group(1)
            genreWithLink = genreWithLink.replace("</span>", "")
            genreWithLink = genreWithLink.replace("<span>", "")
            genreWithLink = re.sub('\s+?<a href=[\w\W]+?>', "", genreWithLink)
            movieGenre = genreWithLink.replace("</a>", "")
            movieGenre = movieGenre.replace("\r\n", " ")
            movieGenre = movieGenre.strip()
        else:
            raise NotImplementedError(
                "ERROR FOUND: change regular expression at getMovieInfoById() for movie genre. Probably FA changed web page structure. Movie ID: " + str(
                    movieID))

        return self.FaMovieExtraInfo(movieTitle, movieYear, movieCountry, movieDirector, movieCast, movieGenre, url=url)

    def getMoviesDumped(self):
        return self.__faMovies

    def getFilledMoviesDumped(self):
        return self.__faMoviesFilled

    def __faVoteDumper(self, queue):
        faHelp = self
        while 1:
            page = queue.get()
            if page is None:
                queue.task_done()
                break  # reached end of queue

            faHelp.getDumpVotesPage(page)
            print("Analyzing vote page: {}".format(page))
            queue.task_done()

    def __faFillMovieInfo(self, queue):
        faHelp = self
        while 1:
            film = queue.get()
            if film is None:
                queue.task_done()
                break  # reached end of queue

            assert isinstance(film, self.FAMovieData)
            extraInfo = faHelp.getMovieInfoById(film.movieID)
            # movieTitle, movieYear, movieCountry, movieDirector, movieCast, movieGenre
            assert isinstance(extraInfo, self.FaMovieExtraInfo)
            film.set_extra_info(extraInfo)

            faHelp.__faMoviesFilled.append(film)

            print("[FA get all data] {}".format(film.get_title().encode('utf-8')))
            queue.task_done()

    def getDumpAllVotes(self):
        numVotes, numPages = self.getNumVotes()
        print("FOUND: {0} movies in {1} pages.".format(numVotes, numPages))

        print("\r\nPushing pages to queue to get all movie information.")
        common.createTrheadedQueue(lambda queue: self.__faVoteDumper(queue), (), range(1, int(numPages) + 1))

        print("\r\nPushing movies to queue to get all movie information.")
        common.createTrheadedQueue(lambda queue: self.__faFillMovieInfo(queue), (), self.__faMovies)

        pass
