#/usr/bin/env python
# avoidr (masscan with exclusive exclusions) - developed by acidvegas in python (https://git.acid.vegas/avoidr)

import ipaddress
import json
import os
import random
import urllib.request

#try:
#	import masscan
#except ImportError:
#	raise SystemExit('error: missing required \'python-masscan\' library (https://pypi.org/project/python-masscan/)')

reserved = {
	'4' : {
		'0.0.0.0/8'          : '"This" network',
		'10.0.0.0/8'         : 'Private networks',
		'100.64.0.0/10'      : 'Carrier-grade NAT - RFC 6598',
		'127.0.0.0/8'        : 'Host loopback',
		'169.254.0.0/16'     : 'Link local',
		'172.16.0.0/12'      : 'Private networks',
		'192.0.0.0/24'       : 'IETF Protocol Assignments',
		'192.0.0.0/29'       : 'DS-Lite',
		'192.0.0.170/32'     : 'NAT64',
		'192.0.0.171/32'     : 'DNS64',
		'192.0.2.0/24'       : 'Documentation (TEST-NET-1)',
		'192.31.196.0/24'    : 'AS112-v4',
		'192.52.193.0/24'    : 'AMT',
		'192.88.99.0/24'     : '6to4 Relay Anycast',
		'192.168.0.0/16'     : 'Private networks',
		'192.175.48.0/24'    : 'AS112 Service',
		'198.18.0.0/15'      : 'Benchmarking',
		'198.51.100.0/24'    : 'Documentation (TEST-NET-2)',
		'203.0.113.0/24'     : 'Documentation (TEST-NET-3)',
		'224.0.0.0/4'        : 'IP Multicast',
		'233.252.0.0/24'     : 'MCAST-TEST-NET',
		'240.0.0.0/4'        : 'Reserved',
		'255.255.255.255/32' : 'Limited Broadcast'
	},
	'6': {
		'::/128'          : 'Unspecified address',
		'::1/128'         : 'Loopback address',
		'::ffff:0:0/96'   : 'IPv4-mapped addresses',
		'::ffff:0:0:0/96' :	'IPv4 translated addresses',
		'64:ff9b::/96'    : 'IPv4/IPv6 translation',
		'64:ff9b:1::/48'  : 'IPv4/IPv6 translation',
		'100::/64'        : 'Discard prefix',
		'2001:0000::/32'  : 'Teredo tunneling',
		'2001:20::/28'    : 'ORCHIDv2',
		'2001:db8::/32'   : 'Addresses used in documentation and example source code',
		'2002::/16'       : 'The 6to4 addressing scheme (deprecated)',
		'fc00::/7'        : 'Unique local address',
		'fe80::/64'       :	'Link-local address',
		'ff00::/8'        : 'Multicast address'
	}
}

asn_queries  = ['754th Electronic Systems Group', 'Air Force Systems Command', 'Army & Navy Building', 'Central Intelligence Agency', 'Defense Advanced Research Projects Agency',
				'Department of Homeland Security', 'Department of Justice', 'Department of Transportation', 'DoD Network Information Center', 'Dod Joint Spectrum Center',
				'FBI Criminal Justice Information Systems', 'Institute of Nuclear Power Operations, Inc', 'Merit Network Inc', 'NASA Ames Research Center', 'NASA Deep Space Network (DSN)',
				'NASA Goddard Space Flight Center', 'Navy Federal Credit Union', 'Navy Network Information Center', 'Nuclear Science and Technology Organisation',
				'Organization for Nuclear Research', 'Root Server Technical Operations', 'Securities & Exchange Commission', 'Securities And Exchange Commission', 'U. S. Air Force',
				'U. S. Bureau of the Census', 'U. S. Department of Transportation', 'U.S. Department of Energy', 'USAISC', 'USDOE, NV Operations Office', 'United States Antarctic Program',
				'United States Coast Guard', 'United States Geological Survey', 'United States Naval Institute', 'United States Nuclear Regulatory Commission',
				'United States Patent and Trademark Office', 'United States Postal Service', 'Internet Exchange', 'Stock Exchange','Federal Emergency Management Agency','Federal Aviation Agency',
				'Federal Energy Regulatory Commission','Federal Aviation Administration','Federal Deposit Insurance Corporation','Federal Reserve Board', 'National Aeronautics and Space Administration',
				'US National Institute of Standards & Technology','Government Telecommunications and Informatics Services','U.S. Dept. of Commerce','U.S. Center For Disease Control and Prevention',
				'U.S. Fish and Wildlife Service','Department of National Defence','U.S. Department of State','Bank of America','JPMorgan Chase & Co','Facebook Inc','Twitter Inc']

def ASNquery(asn):
	head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
	req  = urllib.request.Request(f'https://api.bgpview.io/asn/{asn[2:]}', headers=head)
	data = json.loads(urllib.request.urlopen(req).read())
	return (data['data']['name'], data['data']['description_short'])

def ASNranges(asn, desc):
	head = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
	req  = urllib.request.Request(f'https://api.bgpview.io/asn/{asn[2:]}/prefixes', headers=head)
	data = json.loads(urllib.request.urlopen(req).read())
	ranges = dict()
	for version in ('4','6'):
		if pdata := [x['prefix'] for x in data['data'][f'ipv{version}_prefixes']]:
			ranges[version] = pdata
	return ranges

class Parser:
	def microsoft_office():
		urls = (
			'https://endpoints.office.com/endpoints/USGOVDoD?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7',
			'https://endpoints.office.com/endpoints/USGOVGCCHigh?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7',
			'https://endpoints.office.com/endpoints/worldwide?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7',
			'https://endpoints.office.com/endpoints/China?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7'
		)
		ranges = {'IPv4': list(), 'IPv6': list()}
		for url in urls:
			data = json.loads(urllib.request.urlopen(url).read())
			all_ranges = [item for sublist in [item['ips'] for item in data if 'ips' in item] for item in sublist]
			ranges['IPv4'] += [item for item in all_ranges if ':' not in item]
			ranges['IPv6'] += [item for item in all_ranges if ':' in item]
		return ranges

	def google(): # NOTE: These are non-cloud ranges
		data = json.loads(urllib.request.urlopen('https://www.gstatic.com/ipranges/goog.json').read().decode())
		ranges = {'4': list(), '6': list()}
		ranges['4'] += [item['ipv4Prefix'] for item in data['prefixes'] if 'ipv4Prefix' in item]
		ranges['6'] += [item['ipv6Prefix'] for item in data['prefixes'] if 'ipv6Prefix' in item]
		return ranges

# Main
bad_asn     = json.loads(open('bad.json').read()) if os.path.isfile('bad.json') else dict()
asn_list    = open('asn.txt').readlines()
bad_list    = dict()
database    = dict()
grand_total = {'4': 0, '6': 0}
for item in asn_list:
	item = item.rstrip()
	for query in asn_queries:
		if query.lower() in item.lower():
			asn    = item.split()[0]
			desc   = item.split(' - ')[1] if ' - ' in item else ' '.join(item.split()[2:])
			if asn in bad_asn:
				print('Skippiing bad ASN... ('+asn+')')
			else:
				found = ASNranges(asn, desc)
				if found:
					for version in found:
						total = 0
						for ranges in found[version]:
							total += ipaddress.ip_network(ranges).num_addresses
							grand_total[version] += ipaddress.ip_network(ranges).num_addresses
						print(f'Found \033[32m{len(found[version]):,}\033[0m IPv{version} ranges \033[1;30m({total:,})\033[0m on \033[93m{asn}\033[0m \033[1;30m({desc})\033[0m')
					database[asn] = {'desc': desc, 'ranges': found}
				else:
					print(f'Found \033[1;31m0\033[0m IP ranges on \033[93m{asn}\033[0m \033[1;30m({desc})\033[0m')
					bad_list[asn] = desc
database['reserved'] = {'4': reserved['4'],'6': reserved['6']}
for version in database['reserved']:
	total = 0
	for ranges in database['reserved'][version]:
		total += ipaddress.ip_network(ranges).num_addresses
		grand_total[version] += ipaddress.ip_network(ranges).num_addresses
	print('Found \033[32m{0:,}\033[0m IPv{1} ranges \033[1;30m({2:,})\033[0m on \033[93mRESERVED\033[0m \033[1;30m({3})\033[0m'.format(len(database['reserved'][version]), version, total, database['reserved'][version][ranges]))
with open('db.json', 'w') as fp:
	json.dump(database, fp)
with open('bad.json', 'w') as fp:
	json.dump(bad_list, fp)
total_v4 = ipaddress.ip_network('0.0.0.0/0').num_addresses
total_v6 = ipaddress.ip_network('::/0').num_addresses
print('Total IPv4 Addresses   : {0:,}'.format(total_v4))
print('Total IPv4 After Clean : {0:,}'.format(total_v4-grand_total['4']))
print('Total IPv6 Addresses   : {0:,}'.format(total_v6))
print('Total IPv6 After Clean : {0:,}'.format(total_v6-grand_total['6']))
#mas = masscan.PortScanner() mas.scan('172.0.8.78/24', ports='22,80,8080', arguments='--max-rate 1000') print(mas.scan_result)
