#/usr/bin/env python
# avoidr (masscan with exclusive exclusions) - developed by acidvegas in python (https://git.acid.vegas/avoidr)

asn = open('asn.txt').readlines()

while True:
	query = input('Search: ')
	for i in asn:
		if query.lower() in i.lower():
			print(i.rstrip())
