from html2bbcode.parser import HTML2BBCode
from robobrowser import RoboBrowser
import re

def get_amazon_review():
    '''
    Get the Amazon review for each book in books[]
    '''
    image = review = ''
    results = {}
    browser = RoboBrowser(history=True, 
                    user_agent='Mozilla/5.0 (Windows NT 6.1; rv:30.0) Gecko/20100101 Firefox/30.0')
    url = 'http://www.amazon.com/gp/product/' + str('1593275994')
    browser.open(url)
    html = browser.response.content
    
    tpat = re.compile(r'<span id="productTitle" class="a-size-extra-large">(.*?)</span>')
    results['title'] = tpat.findall(html)[0]
    
    ipat = re.compile(r'data-a-dynamic-image="{&quot;(.*?)&quot;')
    results['image'] = ipat.findall(html)[0]

    rpat = re.compile('<noscript>(.*?)</noscript>', re.DOTALL)
    review = rpat.findall(html)[1]
    results['review'] = html2bbcode(review)
    print results
    return results
        

def html2bbcode(html):
    print 'turning html to bbcode'
    parser = HTML2BBCode()
    bbcode = str(parser.feed(str(html)))
    return bbcode

if __name__ == '__main__':
        get_amazon_review()
