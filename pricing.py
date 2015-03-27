#!/usr/bin/env python

import requests
import json
import re


EC2_PRICING = 'http://a0.awsstatic.com/pricing/1/ec2/linux-od.min.js'
EC2_PRICING_OLD = 'https://a0.awsstatic.com/pricing/1/ec2/previous-generation/linux-od.min.js'

ELB_PRICING = 'http://a0.awsstatic.com/pricing/1/ec2/pricing-elb.min.js'

RDS_STANDARD_MYSQL = 'https://a0.awsstatic.com/pricing/1/rds/mysql/pricing-standard-deployments.min.js'
RDS_STANDARD_POSTGRES = 'https://a0.awsstatic.com/pricing/1/rds/postgresql/pricing-standard-deployments.min.js'
RDS_MULTI_MYSQL = 'https://a0.awsstatic.com/pricing/1/rds/mysql/pricing-multiAZ-deployments.min.js'
RDS_MULTI_POSTGRES = 'https://a0.awsstatic.com/pricing/1/rds/postgresql/pricing-multiAZ-deployments.min.js'

RDS_STANDARD_MYSQL_OLD = 'https://a0.awsstatic.com/pricing/1/rds/mysql/previous-generation/pricing-standard-deployments.min.js'
RDS_STANDARD_POSTGRES_OLD = 'https://a0.awsstatic.com/pricing/1/rds/postgresql/previous-generation/pricing-standard-deployments.min.js'
RDS_MULTI_MYSQL_OLD = 'https://a0.awsstatic.com/pricing/1/rds/mysql/previous-generation/pricing-multiAZ-deployments.min.js'
RDS_MULTI_POSTGRES_OLD = 'https://a0.awsstatic.com/pricing/1/rds/postgresql/previous-generation/pricing-multiAZ-deployments.min.js'


EC2_REGIONS = {
    "apac-sin": u"ap-southeast-1",
    "us-west": u"us-west-1",
    "us-west-2": u"us-west-2",
    "eu-ireland": u"eu-west-1",
    "apac-tokyo": u"ap-northeast-1",
    "us-east": u"us-east-1",
    "apac-syd": u"ap-southeast-2",
    "us-gov-west-1": u"us-gov-west-1",
    "sa-east-1": u"sa-east-1",
    "eu-central-1": u"eu-central-1"
}


def get_json(url):
    j = requests.get(url).content

    if 'callback(' in j:
        j = j.split('callback(')[1][:-2]

    j = re.sub(r"{\s*(\w)", r'{"\1', j)
    j = re.sub(r",\s*(\w)", r',"\1', j)
    j = re.sub(r"(\w):", r'\1":', j)
    return json.loads(j)


def load_pricing():
    pricing = {
        'ec2': {},
        'elb': {},
        'rds': {
            'mysql': {},
            'postgres': {},
            'mysql-multi-az': {},
            'postgres-multi-az': {}
        }
    }

    rds_options = {
        'mysql': [RDS_STANDARD_MYSQL, RDS_STANDARD_MYSQL_OLD],
        'postgres': [RDS_STANDARD_POSTGRES, RDS_STANDARD_POSTGRES_OLD],
        'mysql-multi-az': [RDS_MULTI_MYSQL, RDS_MULTI_MYSQL_OLD],
        'postgres-multi-az': [RDS_MULTI_POSTGRES, RDS_MULTI_POSTGRES_OLD]
    }

    for db_type, urls in rds_options.items():
        for url in urls:
            rds = get_json(url)
            for region in rds['config']['regions']:
                region_name = EC2_REGIONS[region['region']]
                if region_name not in pricing['rds'][db_type].keys():
                    pricing['rds'][db_type][region_name] = {}

                for t in region['types']:
                    for tier in t['tiers']:
                        pricing['rds'][db_type][region_name][tier['name']] = float(tier['prices']['USD'])

    # EC2 Pricing
    for u in [EC2_PRICING_OLD, EC2_PRICING]:
        ec2 = get_json(u)
        for region in ec2['config']['regions']:
            if region['region'] not in pricing['ec2'].keys():
                pricing['ec2'][region['region']] = {}

            for instance_type in region['instanceTypes']:
                for size in instance_type['sizes']:
                    if size['valueColumns'][0]['prices']['USD']:
                        pricing['ec2'][region['region']][size['size']] = float(size['valueColumns'][0]['prices']['USD'])

    # ELB PRICING
    elb = get_json(ELB_PRICING)
    elb_regions = {}

    for region in elb['config']['regions']:
        elb_regions[region['region']] = {}
        for t in region['types']:
            for price in t['values']:
                if price['rate'] == 'perELBHour':
                    elb_regions[region['region']] = float(price['prices']['USD'])

    # ELB Regions have slightly different names in the JSON file
    for region, v in elb_regions.items():
        pricing['elb'][EC2_REGIONS[region]] = v

    print json.dumps(pricing, indent=2)


if __name__ == '__main__':
    load_pricing()
