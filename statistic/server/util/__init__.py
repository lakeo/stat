from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from distutils.version import StrictVersion
import bisect
import functools
import itertools
import operator
import random
import re
import requests
import string
import sys
import time

import unicodedata
import uuid

from dateutil import parser as date_parser
import pytz

import logging

logger = logging.getLogger(__name__)

from statistic.server.config import PARTNER_DEFAULT_TZ

from flask import request

# string util
def random_string(length, characters=string.ascii_letters + string.digits):
    return ''.join(random.SystemRandom().choice(characters) for _ in range(length))


def random_digits(length):
    return random_string(length, characters=string.digits)


def random_uuid_string():
    return str(uuid.uuid4())


def string_join(sep, *data):
    return sep.join(map(str, data))

# performance matters
none_character_table = dict.fromkeys(
    i for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith('P'))


def purge_text(text):
    '''
    >>> purge_text('abc 123 ！？。defg')
    'abc123defg'
    '''
    pure_text = text.translate(none_character_table)
    return re.sub(r'\s', '', pure_text)


# datetime util
def is_aware_datetime(dt):
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def to_aware_datetime(dt, tz):
    if is_aware_datetime(dt):
        return dt.astimezone(tz)
    else:
        return dt.replace(tzinfo=pytz.utc).astimezone(tz)


def parse_datetime(timestr, tz=PARTNER_DEFAULT_TZ):
    """
    >>> parse_datetime('2015-10-13 12:34:56.78910')
    datetime.datetime(2015, 10, 13, 20, 34, 56, 789100, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)

    >>> parse_datetime('2015-10-13 12:34:56.78910+00:00')
    datetime.datetime(2015, 10, 13, 20, 34, 56, 789100, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)

    >>> parse_datetime('2015-10-13 12:34:56.78910+08:00')
    datetime.datetime(2015, 10, 13, 12, 34, 56, 789100, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    """
    return to_aware_datetime(date_parser.parse(timestr), tz)


def parse_date(datestr):
    return date_parser.parse(datestr).date()


def unparse_datetime(dt, fmt=None, tz=PARTNER_DEFAULT_TZ):
    """
    >>> from datetime import datetime

    >>> unparse_datetime(datetime(2015, 1, 1), '%Y-week-%W')
    '2015-week-00'

    >>> dt1 = PARTNER_DEFAULT_TZ.localize(datetime(2015, 10, 13, 12, 34, 56, 789100))
    >>> unparse_datetime(dt1)
    '2015-10-13T12:34:56.789100+08:00'

    >>> unparse_datetime(dt1, fmt='%Y-%m-%d %H:%M:%S')
    '2015-10-13 12:34:56'

    >>> dt2 = datetime(2015, 10, 13, 12, 34, 56, 789100)
    >>> unparse_datetime(dt2)
    '2015-10-13T20:34:56.789100+08:00'

    >>> unparse_datetime(dt2, fmt='%Y-%m-%d %H:%M:%S')
    '2015-10-13 20:34:56'
    """

    aware_dt = to_aware_datetime(dt, tz)
    if fmt is None:
        return aware_dt.isoformat()
    else:
        return aware_dt.strftime(fmt)


def unparse_date(dt, fmt=None):
    if fmt is None:
        return dt.isoformat()
    else:
        return dt.strftime(fmt)


def now():
    return to_aware_datetime(datetime.utcnow(), PARTNER_DEFAULT_TZ)


def start_of_hour(dt=None):
    dt = dt or now()
    return dt.replace(minute=0, second=0, microsecond=0)


def start_of_day(dt=None):
    dt = dt or now()
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt=None):
    dt = dt or now()
    return start_of_day(dt=dt + timedelta(hours=24)) - timedelta(seconds=1)


def start_of_month(dt=None):
    dt = dt or now()
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def start_of_year(dt=None):
    dt = dt or now()
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def start_of_last_hour(dt=None):
    return start_of_hour(dt=start_of_hour(dt) - timedelta(seconds=1))


def start_of_yesterday(dt=None):
    return start_of_day(dt=start_of_day(dt) - timedelta(seconds=1))


def start_of_last_month(dt=None):
    return start_of_month(dt=start_of_month(dt) - timedelta(seconds=1))


def start_of_last_year(dt=None):
    return start_of_year(dt=start_of_year(dt) - timedelta(seconds=1))


def seconds_left_today():
    return int((end_of_day() - now()).total_seconds())


def timestamp_in_ms(dt=None):
    """
    >>> dt = now()
    >>> int(dt.timestamp() * 1000) == timestamp_in_ms(dt)
    True
    """
    if dt:
        ts = to_aware_datetime(dt, pytz.utc).timestamp()
    else:
        ts = time.time()

    return int(ts * 1000)


def is_at_night():
    hour = now().hour
    return not (8 <= hour < 23)


def is_apple_at_work():
    hour = now().hour
    minute = now().minute
    return 2 <= hour < 8 or (hour == 8 and minute <= 30)


def is_apple_at_work_extra():
    current_time = now()
    hour = current_time.hour
    minute = current_time.minute
    if 0 <= hour < 10:
        return True
    if hour == 0 and minute >= 30:
        return True
    else:
        return False


def seconds_to_readable(n_seconds):
    '''
    >>> seconds_to_readable(60 * 2)
    '2分钟'

    >>> seconds_to_readable(60 * 60 * 4.9)
    '4小时'

    >>> seconds_to_readable(60 * 60 * 50)
    '2天'

    '''
    if n_seconds == 0:
        return ''
    if n_seconds < 60:
        return '1分钟'
    elif n_seconds < 60 * 60:
        return '%s分钟' % int(n_seconds / 60)
    elif n_seconds < 60 * 60 * 24:
        return '%s小时' % int(n_seconds / 60 / 60)
    else:
        return '%s天' % int(n_seconds / 60 / 60 / 24)


# data structure util

def flatten(lists):
    return itertools.chain.from_iterable(lists)


def shuffled(elems, keyfn=lambda e: random.random()):
    return sorted(elems, key=keyfn)


# http://stackoverflow.com/a/18411610
def null_first_sorted(iterable, key=lambda x: (x is not None, x), reverse=False):
    '''
    >>> null_first_sorted([2, None, 1])
    [None, 1, 2]

    >>> null_first_sorted(['2', None, '1'], reverse=True)
    ['2', '1', None]
    '''
    return sorted(iterable, key=key, reverse=reverse)


def null_last_sorted(iterable, key=lambda x: (x is None, x), reverse=False):
    '''
    >>> null_last_sorted([2, None, 1])
    [1, 2, None]

    >>> null_last_sorted(['2', None, '1'], reverse=True)
    [None, '2', '1']
    '''
    return sorted(iterable, key=key, reverse=reverse)


# redis util
def redis_key(prefix, oid, what):
    return ':'.join([prefix, oid, what])


def collection_key(what, oid):
    return redis_key('coll', what, oid)


# number
def fix_double_precision(d):
    if d:
        if abs(d) < 1.1e-127:
            return 0
        else:
            return d


def int_or_None(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def random_between(min, max):
    '''
    >>> 100 < random_between(100, 101) < 101
    True
    '''
    return random.random() * (max - min) + min


def random_nearby(x, deviation):
    '''
    >>> 99 < random_nearby(100, 0.01) < 101
    True
    '''
    a, b = (1 - deviation) * x, (1 + deviation) * x
    return random_between(a, b)


def random_with_weight(choices_and_weights):
    choices, weights = zip(*choices_and_weights)
    cumdist = list(itertools.accumulate(weights))
    x = random.random() * cumdist[-1]
    return choices[bisect.bisect(cumdist, x)]


def del_bad_cdn(cdns, bad_cdn):
    if bad_cdn and len(cdns) > 1:
        return [cdn for cdn in cdns if cdn.push_host != bad_cdn]
    else:
        return cdns

# liveapp util

def app_identifier(req, default=None):
    return req.headers.get('X-Zzb-App-Identifier', default)


def client_identifier(req, default=None):
    return req.headers.get('X-Zzb-Device-Identifier', default)


def client_platform(req, default=None):
    return req.headers.get('X-Zzb-Device-Platform', default)


def client_version(req, default=None):
    return req.headers.get('X-Zzb-App-Version', default)


def client_os_version(req, default=None):
    return req.headers.get('X-Zzb-Os-Version', default)


def client_channel(req, default=None):
    return req.headers.get('X-Zzb-Dist-Channel', default)


def client_user_source(req, default=None):
    data = req.get_json()
    if data and isinstance(data, dict) and 'site' in data:
        return 'site'
    return default


def client_model(req, default=None):
    return req.headers.get('X-Zzb-Device-Model', default)


def client_auth_timestamp(req, default=None):
    return req.headers.get('X-Zzb-Auth-Timestamp', default)


def client_auth_signature(req, default=None):
    return req.headers.get('X-Zzb-Auth-Signature', default)


# reform from http://detectmobilebrowsers.com/download/python
def is_mobile(ua):
    if not ua:
        return False

    reg_b = re.compile(
        r"(android|bb\\d+|meego).+mobile|avantgo|bada\\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\\.(browser|link)|vodafone|wap|windows ce|xda|xiino", re.I | re.M)
    reg_v = re.compile(
        r"1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\\-(n|u)|c55\\/|capi|ccwa|cdm\\-|cell|chtm|cldc|cmd\\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\\-s|devi|dica|dmob|do(c|p)o|ds(12|\\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\\-|_)|g1 u|g560|gene|gf\\-5|g\\-mo|go(\\.w|od)|gr(ad|un)|haie|hcit|hd\\-(m|p|t)|hei\\-|hi(pt|ta)|hp( i|ip)|hs\\-c|ht(c(\\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\\-(20|go|ma)|i230|iac( |\\-|\\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\\/)|klon|kpt |kwc\\-|kyo(c|k)|le(no|xi)|lg( g|\\/(k|l|u)|50|54|\\-[a-w])|libw|lynx|m1\\-w|m3ga|m50\\/|ma(te|ui|xo)|mc(01|21|ca)|m\\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\\-2|po(ck|rt|se)|prox|psio|pt\\-g|qa\\-a|qc(07|12|21|32|60|\\-[2-7]|i\\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\\-|oo|p\\-)|sdk\\/|se(c(\\-|0|1)|47|mc|nd|ri)|sgh\\-|shar|sie(\\-|m)|sk\\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\\-|v\\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\\-|tdg\\-|tel(i|m)|tim\\-|t\\-mo|to(pl|sh)|ts(70|m\\-|m3|m5)|tx\\-9|up(\\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\\-|your|zeto|zte\\-", re.I | re.M)

    b = reg_b.search(ua)
    v = reg_v.search(ua[0:4])
    return bool(b or v)


def is_ios(ua):
    reg = re.compile(r"(iPad|iPhone)|iPod")
    r = reg.search(ua)
    return True if r else False

#微信浏览器
def is_micromessenger(ua):
    reg = re.compile(r"(MicroMessenger|micromessenger)")
    r = reg.search(ua)
    return True if r else False


def is_legal_agent(agent):
    if not agent:
        return False

    # mobile header
    reg_m = re.compile(r"zbd")
    # web header
    reg_w = re.compile(r"okhttp\/2\.5\.0")

    m = reg_m.search(agent)
    w = reg_w.search(agent)
    return bool(m or w)


def url_for_app(what, oid=None):
    '''
    >>> url_for_app('users')
    'zzb://users'

    >>> url_for_app('broadcasts', 1234567)
    'zzb://broadcasts/1234567'
    '''
    if oid is None:
        return 'zzb://%s' % what
    else:
        return 'zzb://%s/%s' % (what, oid)


def is_elephant_tv(app_identifier):
    return app_identifier == 'ios:me.bobo.bobo'


def _host_region(host):
    return host.split('.')[0].split('-')[1]


class ClientVersion(StrictVersion):
    '''
    >>> ClientVersion('3.8.11', device_platform='ios') == ClientVersion('3.8.1')
    True

    >>> ClientVersion('3.8.21', device_platform='ios') == ClientVersion('3.8.1')
    True

    >>> ClientVersion('3.8.11') == ClientVersion('3.8.1')
    False

    >>> ClientVersion('3.8.1', device_platform='ios') == ClientVersion('3.8.11', device_platform='ios')
    True
    '''
    def __init__(self, vstring=None, device_platform=None):
        if vstring and device_platform == 'ios':
            index = vstring.rfind('.')
            # len('3.8.2') - '3.8.2'.rfind('.') == 2    # old-style
            # len('3.8.20') - '3.8.20'.rfind('.') == 3  # new-style
            if len(vstring) - index >= 3:
                # new-style iOS 版本：移除 ios 大/小号标志 vstring[index+1]
                vstring = vstring[:index+1] + vstring[index+2:]

        super(ClientVersion, self).__init__(vstring=vstring)


def version_cmp(op, v1, v2, v1_device_platform=None, v2_device_platform=None):
    '''
    >>> version_gt('3.9', '3.8.10')
    True

    >>> version_gt('3.8.10', '3.8.2')
    True

    >>> version_gt('3.8.2', '3.8.1')
    True

    >>> version_eq('3.8.01', '3.8.1')
    True

    >>> version_eq('3.8.0', '3.8')
    True

    >>> version_eq('3.8', '3.8.0')
    True

    >>> version_eq('3.8.11', '3.8.1', v1_device_platform='ios')
    True

    >>> version_eq('3.8.11', '3.8.1', v1_device_platform='ios')
    True

    >>> version_eq('3.8.11', '3.8.1', v1_device_platform='android')
    False

    >>> version_lt('3.8.1', '3.8.2')
    True

    >>> version_lt('3.8.2', '3.8.10')
    True

    >>> version_lt('3.8.10', '3.9')
    True

    '''
    if isinstance(v1, str):
        v1 = ClientVersion(v1, device_platform=v1_device_platform)

    if isinstance(v2, str):
        v2 = ClientVersion(v2, device_platform=v2_device_platform)

    return op(v1, v2)


def version_gt(v1, v2, v1_device_platform=None, v2_device_platform=None):
    return version_cmp(
        operator.gt, v1, v2, v1_device_platform=v1_device_platform, v2_device_platform=v2_device_platform)


def version_ge(v1, v2, v1_device_platform=None, v2_device_platform=None):
    return version_cmp(
        operator.ge, v1, v2, v1_device_platform=v1_device_platform, v2_device_platform=v2_device_platform)


def version_eq(v1, v2, v1_device_platform=None, v2_device_platform=None):
    return version_cmp(
        operator.eq, v1, v2, v1_device_platform=v1_device_platform, v2_device_platform=v2_device_platform)


def version_le(v1, v2, v1_device_platform=None, v2_device_platform=None):
    return version_cmp(
        operator.le, v1, v2, v1_device_platform=v1_device_platform, v2_device_platform=v2_device_platform)


def version_lt(v1, v2, v1_device_platform=None, v2_device_platform=None):
    return version_cmp(
        operator.lt, v1, v2, v1_device_platform=v1_device_platform, v2_device_platform=v2_device_platform)


def bearychat(body, channel='自动报警', markdown=None, attachments=None):
    url = "https://hook.bearychat.com/=bw53H/incoming/e5d24a56bcc5b2ff23ab59bfc76ea465"
    payload = {
        'text': body,
        'markdown': markdown,
        'channel': channel,
        'attachments': attachments,
    }
    data = dict((k, v) for k, v in payload.items() if v is not None)
    requests.post(url, json=data)


def amount_to_cent(amount):
    return int(amount * 100)


def prevent_raise_exception(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)

    return wrapper


def random_red_envelope(minv=2, maxv=30, ev=4):
    return random_between(minv, ev * 2 - minv)

def get_ip():
    return request.remote_addr

if __name__ == '__main__':
    import doctest

    doctest.testmod()

