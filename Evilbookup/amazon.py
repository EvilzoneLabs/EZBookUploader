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
    
def amazonInfo(isbn):
    '''
    Get the Amazon review for each book in books[]
    '''

#    print('Collecting Book info for ISBN: {} from amazon'.format(isbn))
    image = review = ''
    results  = {"title":"", "review":review, "image":image}
    url = 'http://www.amazon.com/gp/product/' + str(isbn)
    br = RoboBrowser(history=True, 
                    user_agent='Mozilla/5.0 (Windows NT 6.1; rv:30.0) Gecko/20100101 Firefox/30.0')
    br.open(url)
    html = br.response.content
    
    #try:
    tpat = re.compile(r'<span id="productTitle" class="a-size-large">(.*?)</span>')
    print tpat.findall(html)
    results['title'] = tpat.findall(html)[0]
    
    ipat = re.compile(r'data-a-dynamic-image="{&quot;(.*?)&quot;')
    results['image'] = ipat.findall(html)[0]

    rpat = re.compile('<noscript>(.*?)</noscript>', re.DOTALL)
    review = rpat.findall(html)[1]
    results['review'] = html2bbcode(review)

    return results
    #except IndexError as e:
        #no results for this ISBN
     #   print('IndexError in amazon')
     #   return results 
        

def html2bbcode(html):
    print 'turning html to bbcode'
    parser = HTML2BBCode()
    bbcode = str(parser.feed(str(html)))
    return bbcode

if __name__ == '__main__':
    #get_amazon_review()
    res = amazonInfo(1783288450)
    print(res)
