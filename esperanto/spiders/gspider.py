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

		self.link_extractor = LinkExtractor(deny=[r'\.wiki(news|pedia|books|media|travel|voyage|source|data)\.org/', r'\.rulit\.me/', r'\.ipernity\.com/', r'\.wiktionary\.org/', r'\bgroups\.io/', r'\.archive\.org/', r'\.ushmm\.org/', r'\.steampowered\.com/'], deny_domains=['wikitrans.net', 'epo.wikitrans.net', 'dan.wikitrans.net', 'eo.wikinews.org', 'eo.wikipedia.org', 'eo.wikibooks.org', 'www.rulit.me', 'www.ipernity.com', 'commons.wikimedia.org', 'eo.wiktionary.org', 'groups.io', 'web.archive.org', 'collections.ushmm.org', 'store.steampowered.com'], unique=True)

		subprocess.run(['sqlite3', 'esperanto.sqlite', '-init', 'schema.sql'], input='')
		self.con = sqlite3.connect('esperanto.sqlite')
		self.db = self.con.cursor()

	def start_requests(self):
		self.db.execute("SELECT q_url FROM sc_queue ORDER BY q_stamp ASC, q_url ASC")
		urls = self.db.fetchall()

		if not urls:
			urls = Path('urls.txt').read_text(encoding='UTF-8')
			urls = re.sub(r'#[^\n]+\n', r'', urls)
			urls = urls.strip().split('\n')
			for url in urls:
				self.db.execute("INSERT OR IGNORE INTO sc_queue (q_url) VALUES (?)", [url])
			self.con.commit()
			self.db.execute("SELECT q_url FROM sc_queue ORDER BY q_stamp ASC, q_url ASC")
			urls = self.db.fetchall()

		for url in urls:
			self.log(f'Queued start {url[0]}')
			yield scrapy.Request(url=url[0], callback=self.parse)

	def parse(self, response):
		body = response.text

		good = False
		if re.search(r'<(?:html|body)\b[^>]*\blang=["\']?eo', body, re.IGNORECASE):
			self.log(f'Esperanto lang=eo {response.url}')
			good = True
		if (len(re.findall(r'[ĈĉĜĝĴĵŜŝŬŭ]', body)) >= 4):
			self.log(f'Esperanto diacritics {response.url}')
			good = True
		'''
		if (len(re.findall(r'[CcGgJjSsUu]x', body)) >= 8):
			self.log(f'Esperanto X-convention {response.url}')
			good = True
		'''
		if (len(re.findall(r'&#(?:264|265|284|285|308|309|348|349|364|365);', body)) >= 4):
			self.log(f'Esperanto entitiy {response.url}')
			good = True
		if (len(re.findall(r'&#[xX](108|109|11C|11D|134|135|15C|15D|16C|16D);', body)) >= 4):
			self.log(f'Esperanto hex-entitiy {response.url}')
			good = True

		if not good:
			self.log(f'Not Esperanto {response.url}')
			self.db.execute("INSERT OR IGNORE INTO sc_queue_not (q_url) VALUES (?)", [response.url])
			self.con.commit()
			return None

		h = hashlib.sha1(response.body).hexdigest()
		self.db.execute("SELECT r_url FROM sc_results WHERE r_hash = ?", [h])
		if self.db.fetchall():
			self.log(f'Seen parse {response.url}')
			# We've already seen this result body
			return None

		headers = ''
		for k,v in response.headers.items():
			headers += f'{k}: {v}\n'

		self.db.execute("INSERT INTO sc_results (r_hash, r_url, r_headers, r_body) VALUES (?, ?, ?, ?)", [h, response.url, headers, body])

		urls = []
		links = self.link_extractor.extract_links(response)
		for link in links:
			if link.nofollow:
				self.log(f'Nofollow {response.url} => {link.url}')
				continue
			link.url = re.sub(r'#.*$', r'', link.url)
			link.url = re.sub(r'///+', r'//', link.url)

			self.db.execute("SELECT q_url FROM sc_queue WHERE q_url = ?", [link.url])
			if self.db.fetchall():
				self.log(f'Seen queue {response.url} => {link.url}')
				continue
			self.db.execute("SELECT q_url FROM sc_queue_not WHERE q_url = ?", [link.url])
			if self.db.fetchall():
				self.log(f'Seen queue_not {response.url} => {link.url}')
				continue
			self.db.execute("SELECT r_url FROM sc_results WHERE r_url = ?", [link.url])
			if self.db.fetchall():
				self.log(f'Seen result {response.url} => {link.url}')
				continue

			self.db.execute("INSERT OR IGNORE INTO sc_queue (q_url) VALUES (?)", [link.url])
			urls.append(link.url)

		self.db.execute("DELETE FROM sc_queue WHERE q_url = ?", [response.url])
		self.con.commit()
		self.log(f'Stored {response.url}')

		for url in urls:
			self.log(f'Queued parse {response.url} => {url}')
			yield scrapy.Request(url=url, callback=self.parse)
