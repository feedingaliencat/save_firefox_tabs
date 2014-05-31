#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Reads the firefox config file 'sessionstore.js' and extracts all the open tabs,
saving urls and titles in a text file and/or in a JSON file, sorted by group of tabs.
'''

import os
import sys
import shutil
import json
import argparse


class Urls(object):
	def __init__(self):
		self._urls = {}
		# The structure is: { group1 : [{'url': url, 'title': title}, {tab2}, {tab3} ], group2 : ...}

		self._groups = {}	# { group1 : name_of_the_group }

	def add(self, groupID, url=' ', title="no_title"):
		if not groupID in self._urls:
			self._urls[groupID] = []

		self._urls[groupID].append({
				'url' : url,
				'title' : title
			})

	def add_group(self, groupID, name):
		if name == '':
			self._groups[groupID] = groupID
		else:
			self._groups[groupID] = name

	def join_group_names(self):
		''' Inner join between _urls and _groups. It modifies, when possible, the group ID with
			the group name. '''
		for g, name in self._groups.items():
			name = name.encode('utf-8')
			if name in self._urls:		# There are two groups with the same title
				name = ' '.join([g, name])
			try:
				self._urls[name] = self._urls.pop(int(g))
			except KeyError:			# Empty group of tabs
				pass

	def to_file(self, file_name='urls.txt'):
		f = open(file_name, 'w')
		for group, tabs in self._urls.items():
			f.write('\n====== {:^15} ======\n'.format(group))
			
			for t in tabs:
				name = t['title'].encode('utf-8')
				url = '{}\t{}\n'.format(name, t['url'])
				f.write(url)

		f.close()

	def to_json(self, file_name='urls.json'):
		f = open(file_name, 'w')
		f.write(json.dumps(self._urls))		# TODO: or dump?
		f.close()


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Save urls and titles of the firefox open tabs')
	parser.add_argument('-f', '--file_path', 
						help="path of the 'sessionstore.js' file")
	parser.add_argument('-o', '--save_text', action='store_true', default=False,
						help='create a textual output file')
	parser.add_argument('-op', '--output_path', default='urls.txt',
						help='choose the path for textual output file')
	parser.add_argument('-j', '--save_json', action='store_true', default=False,
						help='save to a json file')
	parser.add_argument('-jp', '--json_path', default='urls.json',
						help='choose the path for the json file')

	args = parser.parse_args()
# TODO: it would be nice to set -o (or -j) to True, if -op (or -jp) is called

	_USE_TMP_FILE = False

	if not args.file_path:
		_USE_TMP_FILE = True
		my_path = os.path.expanduser('~')+'/.mozilla/firefox'
		subdirs = os.listdir(my_path)

		for d in subdirs:
			if '.default' in d:
				my_path = '/'.join([my_path, d, 'sessionstore.js'])
				break

		shutil.copy(my_path, os.getcwdu()+'/tmp.js')
		args.file_path = 'tmp.js'

	f = open(args.file_path)
	d = json.load(f)
	f.close()

	if _USE_TMP_FILE:
		os.remove(os.getcwdu()+'/tmp.js')

	u = Urls()

#  The structure of 'sessionstore.js' is: d['windows'][0]['tabs'][0]['entries'][0]
	for t in d['windows'][0]['tabs']:
		try:		# some tabs aren't part of any group
			ext = json.loads(t['extData']['tabview-tab'])
			groupID = ext['groupID']
		except KeyError:
			groupID = 'no group tabs'

# In t['entries'] there is the entire story of the tab (next and back pages).
# t['index'] indexes the current page.
# There are tabs without 'entries' (if you open a tab, write an url without sending it).
		try:
			under_tab = t['entries'][t['index']-1]
		except KeyError:
			u.add(groupID, t['userTypedValue'])
		else:
			if 'title' in under_tab:
				u.add(groupID, under_tab['url'], under_tab['title'])
			else:
				u.add(groupID, under_tab['url'])

	try:
		groups = json.loads(d['windows'][0]['extData']['tabview-group'])
	except KeyError:
# if an user doesn't use group of tabs, there won't be tabview-group infos in 'sessionstore.js'
		pass
	else:
		for g, v in groups.items():
			u.add_group(g, v['title'])

	u.join_group_names()

	if args.save_text:
		u.to_file(args.output_path)

	if args.save_json:
		u.to_json(args.json_path)


