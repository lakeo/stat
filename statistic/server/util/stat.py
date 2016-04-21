# coding: utf-8
from sqlalchemy import (
    create_engine, Column, BigInteger, DateTime, Date, Index, text, Enum, Text,
    Boolean, String, Numeric,Integer,
    func, Float, UniqueConstraint, and_)

def getResultFromDB(dburi, sql):
    engine = create_engine(dburi, convert_unicode=True)
    result = engine.execute(sql)
    return result

def getResultFromMultiDB(dburis, sql):
    result = []
    for dburi in dburis:
        tmp = getResultFromDB(dburi, sql)
        if tmp:
            result.extend(tmp)
    return result

def getResultFromShards(sql):
    uris = ['postgres://zzb:drag0ndragon@dbs64/zzb_shard_1',
            'postgres://zzb:drag0ndragon@dbs74/zzb_shard_2',
            'postgres://zzb:drag0ndragon@dbs84/zzb_shard_3',
            'postgres://zzb:drag0ndragon@dbs94/zzb_shard_4',]
    return getResultFromMultiDB(uris, sql)

def getResultFromMISC(sql):
    uri = 'postgres://zzb:drag0ndragon@dbmisc/dbmisc'
    return getResultFromDB(uri, sql)


def writeToFile(filename, data, headers):
    with open(filename, 'w') as f:
        header = '"' + '","'.join(headers) + '"'
        f.write('%s\n' % header)
        for line in data:
            tmp = '"%s"' % line[headers[0]]
            for header in headers[1:]:
                tmp += ',"%s"' % line[header]
                tmp += '\n'
                f.write(tmp)
        f.flush()


