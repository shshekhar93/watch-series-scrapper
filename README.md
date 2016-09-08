# Watch Series Scrapper

Watch Series Scrapper is a commandline tool to download episodes of a series sequentially from a Watch Series site.

### Installation

Watch series scrapper requires python 2.7 to run. Clone this repo and execute the following commands.

To install the dependencies:
```sh
$ pip install -r requirements.txt
```

To download videos on a webpage
```sh
$ python scrapper.py "URL of the page"
```

### Info

The downloaded files will be kept in a directory by name of series. Inside the series' directory, directories will be created recursively for each season and each episode in the season.

**Note:** Directories are created only while downloading a pariticular episode. Unnnecessary directories will not be created.