# Imported Libraries
import string
import random
import redis
import sys
import base64
import json

class UrlShortenerService(object):
    
    # local variables for Redis implementation
    redis_srv = None
    redis_shortened_url_key_fmt = 'shortened.url:%s'
    redis_global_urls_list = 'global:urls'
    redis_shortened_url_visitors_list_fmt = 'visitors:%s:url'
    redis_shortened_url_clicks_counter_fmt = 'clicks:%s:url'

    # our prefix base_url for our url shortener service
    base_url = 'http://rllytny.url/'

    def __init__(self):
        "Initializes self"
        self.redis_srv = redis.StrictRedis(host='localhost', port=6379, db=0)

    # Actionable methods
    def shorten_url(self, long_url):
        # jumbled them up
        url_str_arr = list(long_url)
        random.shuffle(url_str_arr)
        
        # get the last 10 items of the jumbled_url, assuming url is very longer than 20 chars
        if len(url_str_arr) > 20:
            shortened_url = url_str_arr[-10:]
        else:
            shortened_url = url_str_arr

        jumbled_url_suffix = ''.join(shortened_url)

        shortened_url = self.base_url + jumbled_url_suffix

        # encode shortened_url before saving
        encoded_url = encode_base64(shortened_url)

        shortened_url_key = url_string_formatter(self.redis_shortened_url_key_fmt, encoded_url)

        self.redis_srv.set(shortened_url_key, long_url)
        self.redis_srv.lpush(self.redis_global_urls_list, encoded_url)

        return shortened_url, encoded_url

    def expand_url(self, shortened_url):
        shortened_url_key = url_string_formatter(self.redis_shortened_url_key_fmt, shortened_url)
        return self.redis_srv.get(shortened_url_key)

    def visit(self, shortened_url=None, ip_address=None, agent=None, referrer=None):
        visitor_agent = {'ip_address': ip_address, 'agent':agent, 'referrer':referrer}
        
        url_visitors_list = url_string_formatter(self.redis_shortened_url_visitors_list_fmt, shortened_url)
        self.redis_srv.lpush(url_visitors_list, json.dumps(visitor_agent))

        url_clicks_counter = url_string_formatter(self.redis_shortened_url_clicks_counter_fmt, shortened_url)
        return self.redis_srv.incr(url_clicks_counter)

    # Retrieve counter properties from Redis
    def clicks(self, shortened_url = None):
        url_clicks_counter = url_string_formatter(self.redis_shortened_url_clicks_counter_fmt, shortened_url)
        return self.redis_srv.get(url_clicks_counter)

    def recent_visitors(self, shortened_url):
        visitor_agents = []

        url_visitors_list = url_string_formatter(self.redis_shortened_url_visitors_list_fmt, shortened_url)
        for visitor in self.redis_srv.lrange(url_visitors_list, 0, -1):
            visitor_agents.append(json.loads(visitor))
        return visitor_agents

    def short_urls(self):
        return self.redis_srv.lrange(self.redis_global_urls_list, 0, 100)

# End Class Methods

#Utility methods
def url_string_formatter(str_fmt, url):
    return str_fmt % url

#  Base64 Encoding and Decoding functions
def encode_base64(str_to_encode):    
    result = base64.b64encode(str_to_encode)
    return result

def decode_base64(str_to_decode):
    result = base64.b64decode(str_to_decode)
    return result
