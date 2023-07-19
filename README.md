# avoidr
> masscan with exclusive exclusions

![](.screens/preview.png)

## Information
This is still a work in progress.

This is just a little side project I am working on that will search keywords in a database of **Autonomous System Numbers** *(ASN)*. The ASN is then turned into a list of its respective IP ranges that fall under it.

The ranges are all stored in a JSON file for easy parsing. Depending on what you are scanning for, this list can be altered to better suit your needs.

As it stands, there are *4,294,967,296* IPv4 addresses. After excluding reserved, private, & governement ranges, you can drop that number drastically, thus speeding up your scan times.

```
Total IPv4 Addresses   : 4,294,967,296
Total IPv4 After Clean : 3,343,567,221
Total IPv6 Addresses   : 340,282,366,920,938,463,463,374,607,431,768,211,456
Total IPv6 After Clean : 336,289,486,288,049,758,211,573,978,091,720,015,870
```

## Todo
- Do we need parsers for Office/Google from their provided JSON or do all those ranges fall under a single ASN?
- distributed masscan using the masscan python library
- masscan exclude.conf output format *(with comments describing the ranges)*
- possibly find a database that contains all the prefixes behind an ASN *(bgpview heavily throttles and can only handle 1 ASN at a time)* *(for now a bad.json is generated to list empty ASN's)*
- Seperate queries by sectors *(Government, social media, financial institutons, schools, etc)*

___

###### Mirrors
[acid.vegas](https://git.acid.vegas/avoidr) • [GitHub](https://github.com/acidvegas/avoidr) • [GitLab](https://gitlab.com/acidvegas/avoidr) • [SuperNETs](https://git.supernets.org/acidvegas/avoidr)
