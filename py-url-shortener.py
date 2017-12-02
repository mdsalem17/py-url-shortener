# TODOs - to place in a setup folder
# Importing libraries
import string
import random
import redis
import sys
import base64
import json

class UrlShortenerService:
    
    # local variables for redis implementation
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

        # TODOS
        encoded_url = encode_base64(jumbled_url_suffix)
        decoded_url = decode_base64(encoded_url)

        shortened_url_key = url_string_formatter(self.redis_shortened_url_key_fmt, shortened_url)

        self.redis_srv.set(shortened_url_key, long_url)
        self.redis_srv.lpush(self.redis_global_urls_list, shortened_url)

        return shortened_url, encoded_url, decoded_url

    def expand_url(self, shortened_url):
        shortened_url_key = url_string_formatter(self.redis_shortened_url_key_fmt, shortened_url)
        return self.redis_srv.get(shortened_url_key)

    def visit(self, shortened_url=None, ip_address=None, agent=None, referrer=None):
        visitorAgent = {'ip_address': ip_address, 'agent':agent, 'referrer':referrer}
        
        url_visitors_list = url_string_formatter(self.redis_shortened_url_visitors_list_fmt, shortened_url)
        self.redis_srv.lpush(url_visitors_list, json.dumps(visitorAgent))

        url_clicks_counter = url_string_formatter(self.redis_shortened_url_clicks_counter_fmt, shortened_url)
        return self.redis_srv.incr(url_clicks_counter)

    # Retrieve counter properties from Redis
    def clicks(self, shortened_url = None):
        url_clicks_counter = url_string_formatter(self.redis_shortened_url_clicks_counter_fmt, shortened_url)
        return self.redis_srv.get(url_clicks_counter)

    def recent_visitors(self, shortened_url):
        visitorAgents = []

        url_visitors_list = url_string_formatter(self.redis_shortened_url_visitors_list_fmt, shortened_url)
        for v in self.redis_srv.lrange(url_visitors_list, 0, -1):
            visitorAgents.append(json.loads(v))
        return visitorAgents

    def short_urls(self):
        return self.redis_srv.lrange(self.redis_global_urls_list, 0, 100)

# End Class Methods

#Utility methods
def url_string_formatter(str_fmt, url):
    return str_fmt % url

#  Base64 Encoding/Decoding functions
def encode_base64(toencode):    
    result = base64.b64encode(toencode)
    return result

def decode_base64(todecode):
    result = base64.b64decode(todecode)
    return result

def readInputFile(text_file, url_shortener_service):
    with open(text_file, 'r') as infile:
        for line in infile:
            # Ignore any comments in file
            if '#' not in line[0]:
                shortened_url, encoded_url, decoded_url = url_shortener_service.shorten_url(line)
                expanded_url = url_shortener_service.expand_url(shortened_url)

                print("ShortenedURL: {0}; ExpandedURL: {1}".format(shortened_url, expanded_url))
                print(".... EncodedURL: {0}; DecodedURL: {1}".format(encoded_url, decoded_url))
    return

def visitors_visiting(url_shortener_service):

    print('Visitors visiting...')

    for i in range(0, 5):    
        for d in url_shortener_service.short_urls():
            print('... %s' % d)
            url_shortener_service.visit(d)

    print('Recent Visitors')

    for d in url_shortener_service.short_urls():
        print('... %s' % d)
        visitor_agents = url_shortener_service.recent_visitors(d)
        print('Total recent vistors for {0} are {1}'.format(d, len(visitor_agents)))

    return

def main():
    
    # inistantiate url_shorteer_service
    url_shortener_service = UrlShortenerService()

    #read text input file
    readInputFile('urls-to-read.txt', url_shortener_service)

    #Web visitor activity being tracking...
    visitors_visiting(url_shortener_service)

if __name__ == '__main__':
    main()