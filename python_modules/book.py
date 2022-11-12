
# coding: utf-8



import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import Request,urlopen
import urllib
import re
from goodreads import client
from tqdm import tqdm


# API KEYS


API_KEY=""
API_SEC=""


# File Imports


#master book list
df=pd.read_csv(r"C:\Users\Goose\Documents\Goodreads-20170907T175938Z-001\Goodreads\Data\book_list.csv")
unique_books=df


# Variables



user_agent="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
headers={'User-Agent': user_agent}


class book:
    
    def __init__(self, book_id, title=None,author=None):
        self.id = book_id
        self.title = title
        #obtain title from goodreads info if not in DB
        self.author= author
        self.exists = book_id in unique_books['book_id'].values #exists in my DB
        self.list_bool=type(self.id)==list
            
        if (self.list_bool==True and self.exists==True):
            self.title=list(self.book_exist()['title'].values)
            self.author=list(self.book_exist()['author'].values)
            
        elif (self.list_bool==False and self.exists==True):
            self.title=self.book_exist()['title'].values[0]
            self.author=self.book_exist()['author'].values[0]
            
            
            
        if self.title is not None:
            self.url_title=urllib.parse.quote(self.title)
            
        if self.author is not None:
            self.url_author=urllib.parse.quote(self.author)
            
        #gc = client.GoodreadsClient(API_KEY, API_SEC)
        #gc.author(self.id)
            
        
     #create method to find id if only name is given
    
    def book_exist(self):
        #Function to check if author exists in personal DB
        #check for list of IDs
        if self.list_bool:
            df=unique_books[unique_books['book_id'].isin(self.id)]
        else:
            df=unique_books[unique_books['book_id'].isin([self.id])]
            
        return df



    def goodreads_info(self):
        
        URL="https://www.goodreads.com/book/show/"+str(self.id)+".xml?key="+API_KEY
        soup = BeautifulSoup(urlopen(URL),'xml') #find a way to only return part of this page??
        orig_pub_year=soup.original_publication_year.string
        avg_rating=soup.average_rating.string
        ratings_count=soup.ratings_count.string
        #get title 
        original_title=soup.original_title.string
        publisher=soup.publisher.string
        description=soup.description.string
        #orig_language_id=soup.original_language_id.string #sparse data field - Use different metric
        
        #clause for id arrays
        
        #Function for finding author information off goodreads
        #check what you want to return using radio button etc.

        d={"orig_pub_year":orig_pub_year,
           "book_id":self.id,
           "avg_rating":avg_rating,
           "ratings_count":ratings_count,
           "original_title":original_title,
           "publisher":publisher,
           "description":description,
          }
           #"image_url":image_url}
        #pd.DataFrame(pd.Series(d)).T
        #returns dictionary
        return d
    
    #google searches:
    #check master file before doing google searches
    
    def url_search(self, url):
        req = Request(url, headers=headers)
        page = urlopen(req)
        soup = BeautifulSoup(page, 'html.parser')
        
        try:
            res = soup.find('div', attrs={'class':'_XWk'})
            return res.text
        
        except:
            return None
    
    def first_published(self):
        url='http://www.google.com/search?q=when+was+'+self.url_title+'+'+self.url_author+'first+published%3F&hl=en'
        return self.url_search(url)


# Individual Functions



def book_scrape(link,d):
    d.append({'book_id': link.book.id.string, 'author_id': link.author.id.string, 'author': link.find('name').string,
              'title':link.title.string, 'num_pages':link.num_pages.string,
              'publication_year':link.publication_year.string,
              'book_image_link':link.image_url.string,#don't bother: https://s.gr-assets.com/assets/nophoto/book/111x148-bcc042a9c91a29c1d680899eff700a03.png
              'date_read':link.read_at.string,
              'my_rating':link.rating.string})




def review_scrape(soup,d,entire):
    for link in (soup.find_all('review')):
        if entire==True:
            book_scrape(link,d)
            
        elif entire==False:
            b=book(int(link.book.id.string))
            if b.exists==False:
                book_scrape(link,d)




def read_book_pull(entire):
    URL="https://www.goodreads.com/review/list/51672399.xml?key="+API_KEY+"&amp;v=2&amp;shelf=read&amp;sort=date_read"
    soup = BeautifulSoup(urlopen(URL),'xml')
    TOTAL=int(soup.reviews.attrs['total']) #number of books read
    
    if entire==True:
        pages=int(TOTAL/10 +1)
        
    elif entire==False:
        #crude calculation: needs to assume book_list data is complete
        new_books=TOTAL-len(unique_books)
        pages=int(new_books/10 +1)
        
    d = []
    review_scrape(soup,d,entire)
    for i in tqdm(range(2,pages+1)):
        URL="https://www.goodreads.com/review/list/51672399.xml?key="+API_KEY+"&amp;v=2&amp;shelf=read&amp;sort=date_read&amp;page="+str(i)
        soup = BeautifulSoup(urlopen(URL),'xml')
        review_scrape(soup,d,entire)
        
    return pd.DataFrame(d)

