import sys
import os
from urlparse import urlparse
from urlparse import parse_qs
from base64 import b64decode
import requests
import bs4
import youtube_dl
import utils

def debug(txt):
	print txt

class Scrapper:
	def __init__(self, opts):
		self.url = ''
		self.type = ''
		self.host = ''
		self.html = None
		if len(sys.argv) > 1:
			self.url = str(sys.argv[1]).strip()
			try:
				self.url.index('/episode/')
				self.type = 'episode'
			except:
				self.type = 'season'
			parsed_uri = urlparse(self.url)
			self.host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

			self.seriesName, seasonNum, episodeNum = Scrapper.getEpisodeInfoFromPath(parsed_uri.path)
			debug('series is ' + self.seriesName)
			if self.type == 'season':
				self.getSeasonPage()
			else:
				self.allSeasons = {seasonNum: {episodeNum: self.url}}

	def getSeasonPage(self):
		if self.url == '' or self.type == '':
			return None

		try:
			res = requests.get(self.url)
			res.raise_for_status()
		except requests.exceptions.RequestException:
			return None

		debug('request complete')
		self.html = bs4.BeautifulSoup(res.text, 'html.parser')
		debug('parse complete')
		return self.extractEpisodePages()

	def extractEpisodePages(self):
		if self.html == None:
			return None

		seasons = {}
		allSeasonsHtml = self.html.select('div[itemprop="season"]')
		for seasonHtml in allSeasonsHtml:
			seasonName = Scrapper.getNameFromHtml(seasonHtml)
			if seasonName == None:
				pass # This part has no season name. Go to next.

			debug('Getting list of episodes in season ' + str(seasonName))
			seasons[seasonName] = Scrapper.getEpisodeLinksFromHtml(seasonHtml, self.host)
			debug('Found ' + str(len(seasons[seasonName])) + ' episodes')

		self.allSeasons = seasons

	def startDownload(self):
		if(len(self.allSeasons) < 1):
			print 'Nothing to download'
			return

		print "\nStarting download.."
		utils.mnchdir(self.seriesName) # This might raise exception.

		seasonNames = self.allSeasons.keys()
		seasonNames.sort()
		for seasonName in seasonNames:
			print '\nDownloading season', seasonName 
			utils.mnchdir('s' + str(seasonName))

			season = self.allSeasons[seasonName]
			episodeNumbers = season.keys()
			episodeNumbers.sort()
			for episodeNumber in episodeNumbers:
				print '\n\tDownloading episode', episodeNumber
				utils.mnchdir('e' + str(episodeNumber))
				self.downloadEpisode(season[episodeNumber])
				os.chdir('../')

			os.chdir('../')

	def downloadEpisode(self, url):
		debug('\tDownloading episode page')
		try:
			res = requests.get(url)
			res.raise_for_status()
		except requests.exceptions.RequestException:
			print '\tFailed!'
			return

		episodePageHtml = bs4.BeautifulSoup(res.text, 'html.parser')
		links = episodePageHtml.select('div[id="linktable"] a[class="buttonlink"]')
		debug('\tEpisode page parsed')
		for link in links:
			if link['title'].lower() != 'sponsored':
				ret = self.downloadEpisodeFromLink(self.host + link['href'])
				if(ret == True):
					return
				else:
					debug('\tThis Download link failed! Trying another.')
		print '\tFailed! None of the links worked.'
		return 

	def downloadEpisodeFromLink(self, url):
		debug('\tFetching download link ' + url)
		qs = parse_qs(urlparse(url).query)
		if len(qs) > 0:
			for key in qs:
				val = qs[key][0]
				try:
					videoLink = b64decode(val)
					urlTest = urlparse(videoLink)
					if urlTest.netloc != '' and urlTest.path != '':
						return self.fetchWithYoutubeDl(videoLink)
				except TypeError:
					pass
		try:
			res = requests.get(url)
			res.raise_for_status()
		except requests.exceptions.RequestException:
			print '\tFailed!'
			return False

		videoLink = None
		linkPageHtml = bs4.BeautifulSoup(res.text, 'html.parser').select('.fullwrap')
		if len(linkPageHtml) < 1:
			return False
		linkPageHtml = linkPageHtml[0]
		videoIframe = linkPageHtml.select('#video-embed iframe')
		if len(videoIframe) < 1:
			videoIframe = linkPageHtml.select('.video-embed iframe')

		if len(videoIframe) > 0:
			videoLink = videoIframe[0]['src']

		if videoLink == None:
			return False

		return self.fetchWithYoutubeDl(videoLink)

	def fetchWithYoutubeDl(self, url):
		print '\t\tfetching with youtubedl', url
		ydlOpts = {}
		with youtube_dl.YoutubeDL(ydlOpts) as ydl:
			try:
				result = ydl.extract_info(url, download=True)
				return True
			except Exception, e:
				print 'wtf', str(e)
				pass
		return False


	@staticmethod
	def getNameFromHtml(html):
		seasonNameHtml = html.select('a[itemprop="url"] span[itemprop="name"]')
		if (len(seasonNameHtml) < 1):
			# We didn't find the season number. Let this go.
			return None;
		return int(seasonNameHtml[0].text.strip()[7:]) # Remove 'Season '

	@staticmethod
	def getEpisodeLinksFromHtml(html, prefix=None):
		if(prefix == None or type(prefix) != str):
			prefix = ''

		htmlItems = html.select('[itemprop="episode"]')
		episodes = {}
		for htmlItem in htmlItems:
			episodeNumberHtml = htmlItem.select('meta[itemprop="episodenumber"]')
			try:
				episodenumber = episodeNumberHtml[0]['content']
			except IndexError, AttributeError:
				pass

			episodeUrlHtml = htmlItem.select('meta[itemprop="url"]')
			try:
				episodeUrl = episodeUrlHtml[0]['content']
			except IndexError, AttributeError:
				pass
			episodes[int(episodenumber)] = prefix + episodeUrl
		return episodes

	@staticmethod
	def getEpisodeInfoFromPath(path):
		filename = path[path.rfind('/') + 1:].lower()
		seasonNum = 0
		episodeNum = 0
		try:
			filename = filename[:filename.rindex('.')]
			episodeInfo = filename[filename.rindex('_s') + 1 :]
			filename = filename[:filename.rindex('_s')]
			seasonNum = int(episodeInfo[1:episodeInfo.rindex('_e')])
			episodeNum = int(episodeInfo[episodeInfo.rindex('_e') + 2 :])
		except ValueError:
			pass

		seriesName = filename
		return seriesName, seasonNum, episodeNum
		

if __name__ == "__main__":
	scrapper_opts = {}
	scrapper = Scrapper(scrapper_opts)
	scrapper.startDownload()
