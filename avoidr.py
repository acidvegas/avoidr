#/usr/bin/env python
# avoidr (masscan with exclusive exclusions) - developed by acidvegas in python (https://git.acid.vegas/avoidr)

import hashlib
import ipaddress
import json
import logging
import os
import sys
import time
import urllib.request
from zipfile import ZipFile

# Globals
grand_total = {'4': 0, '6': 0}
results     = dict()

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def calculate_hash(path):
	'''
	Calculate the SHA1 hash of a file.
	
	:param path: The path to the file to hash.
	'''
	hash_sha1 = hashlib.sha1()
	with open(path, 'rb') as f:
		for chunk in iter(lambda: f.read(4096), b''):
			hash_sha1.update(chunk)
	return hash_sha1.hexdigest()


def download_file(url: str, dest_filename: str, chunk_size: int = 1024*1024):
    '''
    Download a file from a given URL in chunks and save to a destination filename.

    :param url: The URL of the file to download
    :param dest_filename: The destination filename to save the downloaded file
    :param chunk_size: Size of chunks to download. Default is set to 1MB.
    '''
    with urllib.request.urlopen(url) as response:
        total_size = int(response.getheader('Content-Length').strip())
        downloaded_size = 0
        with open(dest_filename, 'wb') as out_file:
            while True:
                start_time = time.time()
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                downloaded_size += len(chunk)
                out_file.write(chunk)
                end_time = time.time()
                speed = len(chunk) / (end_time - start_time)
                progress = (downloaded_size / total_size) * 100
                sys.stdout.write(f'\rDownloaded {downloaded_size} of {total_size} bytes ({progress:.2f}%) at {speed/1024:.2f} KB/s\r')
                sys.stdout.flush()
            print()


def get_url(url) -> str:
	'''
	Get the contents of a URL.
	
	:param url: The URL to get the contents of.
	'''
	data = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'Avoidr/1.0 (https://git.acid.vegas/avoidr)'}
	req = urllib.request.Request(url, headers=data)
	return urllib.request.urlopen(req, timeout=10).read().decode()


def update_database():
	'''Update the ASN database.'''

	logging.info('Checking for database updates...')

	DB = 'databases/fullASN.json.zip'
	update = False
	os.makedirs('databases', exist_ok=True)

	if not os.path.exists(DB):
		update = True
	else:
		old_hash = calculate_hash(DB)
		new_hash = json.loads(get_url('https://api.github.com/repos/ipapi-is/ipapi/contents/'+DB))['sha']
		if old_hash != new_hash:
			update = True

	if update:
		logging.info('Updating database...')
		for OLD_DB in (DB, DB[:-4]):
			if os.path.exists(OLD_DB):
				os.remove(OLD_DB)
		download_file('https://github.com/ipapi-is/ipapi/raw/main/'+DB, DB)
		with ZipFile(DB) as zObject:
			zObject.extract(DB[10:-4], 'databases')
	else:
		logging.info('Database is up-to-date!')



def process_asn(data: dict):
	'''
	Proccess an ASN and add it to the results.
	
	:param data: The ASN data to process.
	'''

	title = data['descr'] if 'org' not in data else data['descr'] + ' / ' + data['org']
	results[data['asn']] = {'name': title, 'ranges': dict()}

	if 'prefixes' in data and not args.ipv6:
		results[data['asn']]['ranges']['4'] = data['prefixes']
		total = total_ips(data['prefixes'])
		grand_total['4'] += total
		logging.info('Found \033[93mAS{0}\033[0m \033[1;30m({1})\033[0m containing \033[32m{2:,}\033[0m IPv4 ranges with \033[36m{3:,}\033[0m total IP addresses'.format(data['asn'], title, len(data['prefixes']), total))

	if 'prefixesIPv6' in data and not args.ipv4:
		results[data['asn']]['ranges']['6'] = data['prefixesIPv6']
		total = total_ips(data['prefixesIPv6'])
		grand_total['6'] += total
		logging.info('Found \033[93mAS{0}\033[0m \033[1;30m({1})\033[0m containing \033[32m{2:,}\033[0m IPv6 ranges with \033[36m{3:,}\033[0m total IP addresses'.format(data['asn'], title, len(data['prefixesIPv6']), total))


def total_ips(ranges: list) -> int:
	'''
	Calculate the total number of IP addresses in a list of CIDR ranges.
	
	:param ranges: The list of CIDR ranges to calculate the total number of IP addresses for.
	'''
	return sum(ipaddress.ip_network(cidr).num_addresses for cidr in ranges)



# Main
if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='masscan with exclusive exclusions')
	parser.add_argument('-4', '--ipv4', help='process IPv4 addresses only', action='store_true')
	parser.add_argument('-6', '--ipv6', help='process IPv6 addresses only', action='store_true')
	parser.add_argument('-x', '--exclude', help='create exclusions for masscan instead of a json output', action='store_true')
	parser.add_argument('-s', '--search', help='comma seperated strings to search (no output file)', type=str)
	parser.add_argument('-u', '--update', help='update the ASN database', action='store_true')

	args = parser.parse_args()

	if args.update or not os.path.exists('databases/fullASN.json'):
		update_database()

	asn_data = json.loads(open('databases/fullASN.json').read())

	if args.search:
		queries = args.search.split(',')
	else:
		queries = [line.rstrip() for line in open('custom.txt').readlines()]

	logging.debug(f'Searching {len(queries):,} queries against {len(asn_data):,} ASNs...')

	for asn in asn_data:
		for field in [x for x in asn_data[asn] if x in ('descr','org')]:
			if [x for x in queries if x.lower() in asn_data[asn][field].lower()]:
				if asn_data[asn]['asn'] not in results:
					process_asn(asn_data[asn])
					break

	if not args.search:
		os.makedirs('output', exist_ok=True)

		if args.exclude:
			with open('output/exclude.conf', 'w') as fp:
				for item in results:
					fp.write(f'# AS{item} - {results[item]["name"]}\n')
					for version in results[item]['ranges']:
						for _range in results[item]['ranges'][version]:
							fp.write(_range+'\n')
					fp.write('\n')
		else:
			with open('output/out.json', 'w') as fp:
				json.dump(results, fp)
	else:
		logging.info('Add these to your custom.txt file to create output files...')

	total_v4 = ipaddress.ip_network('0.0.0.0/0').num_addresses
	total_v6 = ipaddress.ip_network('::/0').num_addresses
	print('Total IPv4 Addresses   : {0:,}'.format(total_v4))
	print('Total IPv4 After Clean : {0:,}'.format(total_v4-grand_total['4']))
	print('Total IPv6 Addresses   : {0:,}'.format(total_v6))
	print('Total IPv6 After Clean : {0:,}'.format(total_v6-grand_total['6']))
