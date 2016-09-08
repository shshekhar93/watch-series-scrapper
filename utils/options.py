import argparse

def parse_args():
	parser = argparse.ArgumentParser(description='Download series from watch-series sites')
	parser.add_argument('url', metavar='url', type=str, help='url to download the series from')
	parser.add_argument('--start', metavar='start', type=str, help='episode to start at in form s[N]e[N], eg s1e1')
	args = parser.parse_args()
	args.startSeason = 0
	args.startEpisode = 0
	if args.start != None:
		try:
			sindex = args.start.index('s')
			eindex = args.start.index('e')
			args.startSeason = int(args.start[sindex + 1 : eindex])
			args.startEpisode = int(args.start[eindex + 1 :])
		except ValueError:
			pass
		except IndexError:
			pass
	return args