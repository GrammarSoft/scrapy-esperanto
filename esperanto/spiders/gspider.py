import os
import subprocess
import sqlite3
import regex as re
import hashlib
from pathlib import Path
from scrapy.linkextractors import LinkExtractor
import scrapy

class GSpider(scrapy.Spider):
	name = "gspider"

	link_extractor = None
	con = None
	db = None

	def __init__(self, category=None, *args, **kwargs):
		super(GSpider, self).__init__(*args, **kwargs)

		dir = os.path.dirname(__file__)
		os.chdir(dir)

		self.link_extractor = LinkExtractor(deny_domains=['wikitrans.net', 'epo.wikitrans.net', 'dan.wikitrans.net'], unique=True)

		subprocess.run(['sqlite3', 'spider.sqlite', '-init', 'schema.sql'], input='')
		self.con = sqlite3.connect('spider.sqlite')
		self.db = self.con.cursor()

	def start_requests(self):
		self.db.execute("SELECT q_url FROM sc_queue ORDER BY q_stamp ASC, q_url ASC")
		urls = self.db.fetchall()

		if not urls:
			urls = Path('urls.txt').read_text(encoding='UTF-8')
			urls = re.sub(r'#[^\n]+\n', r'', urls)
			urls = urls.strip().split('\n')
			for url in urls:
				self.db.execute("INSERT INTO sc_queue (q_url) VALUES (?)", [url])
			self.con.commit()
			self.db.execute("SELECT q_url FROM sc_queue ORDER BY q_stamp ASC, q_url ASC")
			urls = self.db.fetchall()

		for url in urls:
			self.log(f'Queued {url[0]}')
			yield scrapy.Request(url=url[0], callback=self.parse)

	def parse(self, response):
		body = response.text

		h = hashlib.sha1(response.body).hexdigest()
		self.db.execute("SELECT r_url FROM sc_results WHERE r_hash = ?", [h])
		rows = self.db.fetchall()
		if rows:
			self.log(f'Seen {response.url}')
			# We've already seen this result body
			return None

		headers = ''
		for k,v in response.headers.items():
			headers += f'{k}: {v}\n'

		self.db.execute("INSERT INTO sc_results (r_hash, r_url, r_headers, r_body) VALUES (?, ?, ?, ?)", [h, response.url, headers, body])

		self.db.execute("DELETE FROM sc_queue WHERE q_url = ?", [response.url])
		self.con.commit()
		self.log(f'Stored {response.url}')
		return None
