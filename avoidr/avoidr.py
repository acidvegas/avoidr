#/usr/bin/env python
# avoidr (masscan with exclusive exclusions) - developed by acidvegas in python (https://git.acid.vegas/avoidr)

import hashlib
import ipaddress
import json
import os
import urllib.request
from zipfile import ZipFile

# Globals
grand_total = {'4': 0, '6': 0}
results     = dict()


def calculate_hash(path):
	''' Calculate the SHA1 hash of a file. '''
	hash_sha1 = hashlib.sha1()
	with open(path, 'rb') as f:
		for chunk in iter(lambda: f.read(4096), b''):
			hash_sha1.update(chunk)
	return hash_sha1.hexdigest()


def get_url(url, git=False) -> str:
	''' Get the contents of a URL. '''
	data = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
	if git:
		data['Accept'] = 'application/vnd.github.v3+json'
	req = urllib.request.Request(url, headers=data)
	return urllib.request.urlopen(req, timeout=10).read().decode()


def update_database():
	''' Update the ASN database.  '''
	DB = 'databases/fullASN.json.zip'
	try:
		os.mkdir('databases')
	except FileExistsError:
		pass
	if os.path.exists(DB):
		old_hash = calculate_hash(DB)
		new_hash = json.loads(get_url('https://api.github.com/repos/ipapi-is/ipapi/contents/'+DB))['sha']
		if old_hash != new_hash:
			print('[~] New database version available! Downloading...')
			os.remove(DB)
			if os.path.exists(DB[:-4]):
				os.remove(DB[:-4])
			urllib.request.urlretrieve('https://github.com/ipapi-is/ipapi/raw/main/'+DB, DB)
			with ZipFile(DB) as zObject:
				zObject.extract(DB[10:-4], 'databases')
	else:
		print('[~] Downloading missing database...')
		urllib.request.urlretrieve('https://github.com/ipapi-is/ipapi/raw/main/'+DB, DB)
		if os.path.exists(DB[:-4]):
			os.remove(DB[:-4])
		with ZipFile(DB) as zObject:
			zObject.extract(DB[10:-4], 'databases')


def process_asn(data):
	''' Process an ASN. '''
	if data['asn'] not in results:
		title = data['descr'] if 'org' not in data else data['descr'] + ' / ' + data['org']
		results[data['asn']] = {'name': title, 'ranges': dict()}
		if 'prefixes' in data:
			results[data['asn']]['ranges']['4'] = data['prefixes']
			total = total_ips(data['prefixes'])
			grand_total['4'] += total
			print('Found \033[93mAS{0}\033[0m \033[1;30m({1})\033[0m containing \033[32m{2:,}\033[0m IPv4 ranges with \033[36m{3:,}\033[0m total IP addresses'.format(data['asn'], title, len(data['prefixes']), total))
		if 'prefixesIPv6' in data:
			results[data['asn']]['ranges']['6'] = data['prefixesIPv6']
			total = total_ips(data['prefixesIPv6'])
			grand_total['6'] += total
			print('Found \033[93mAS{0}\033[0m \033[1;30m({1})\033[0m containing \033[32m{2:,}\033[0m IPv6 ranges with \033[36m{3:,}\033[0m total IP addresses'.format(data['asn'], title, len(data['prefixesIPv6']), total))


def total_ips(ranges, total=0):
	for _range in ranges:
		total += ipaddress.ip_network(_range).num_addresses
	return total


def write_exclusions(asn_list, exclusions_file='exclusions.conf'):
	''' Write masscan exclusions file. '''
	exclusions = []
	for asn in asn_list:
		name = asn_list[asn]['name']
		ranges = asn_list[asn]['ranges']

		exclusions.append(f'# {name}')
		for proto in ranges:
			exclusions.extend(ranges[proto])

	with open(exclusions_file, 'w') as fp:
		fp.write('\n'.join(exclusions))


def main():
	print('[~] Checking for database updates...')
	update_database()

	data    = json.loads(open('databases/fullASN.json').read())
	queries = [item.rstrip() for item in open('custom.txt').readlines()]

	print('[~] Searching {len(queries):,} queries against {len(data):,} ASNs...')
	for item in data:
		for field in [x for x in data[item] if x in ('descr','org')]:
			if [x for x in queries if x.lower() in data[item][field].lower()]:
				process_asn(data[item])
				break

	with open('out.json', 'w') as fp:
		json.dump(results, fp)

	write_exclusions(results)

	total_v4 = ipaddress.ip_network('0.0.0.0/0').num_addresses
	total_v6 = ipaddress.ip_network('::/0').num_addresses
	print('Total IPv4 Addresses   : {0:,}'.format(total_v4))
	print('Total IPv4 After Clean : {0:,}'.format(total_v4-grand_total['4']))
	print('Total IPv6 Addresses   : {0:,}'.format(total_v6))
	print('Total IPv6 After Clean : {0:,}'.format(total_v6-grand_total['6']))
	print('Exclusions written to exclusions.conf')


if __name__ == '__main__':
	main()
