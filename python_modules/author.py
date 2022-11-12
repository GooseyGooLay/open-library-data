
# coding: utf-8

# In[1]:


import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import Request,urlopen
import urllib
import requests
import re
from goodreads import client
from geopy.geocoders import Nominatim, GoogleV3, GeoNames


# API KEYS



API_KEY=""
API_SEC=""
google_api=""


# File Imports



#master author list
#just load unique list instead
df=pd.read_csv(r"C:\Users\Goose\Documents\Goodreads-20170907T175938Z-001\Goodreads\Data\authors_list.csv")


# Variables



unique_authors=df.groupby('author_id').first().reset_index()




user_agent="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
headers={'User-Agent': user_agent}


# Geolocators



geolocator = Nominatim()
geolocator2=GoogleV3(api_key=google_api)
geolocator3= GeoNames(username='GooseyGooLay')




class author:
    
    def __init__(self, author_id, author_name=None):
        self.id = author_id
        self.name = author_name
        #add in exists field like book class
        self.exists = self.id in unique_authors['author_id'].values
        self.list_bool=type(self.id)==list
            
        if (self.list_bool==True and self.exists==True):
            self.name=list(self.author_exist()['author'].values)
            
        elif (self.list_bool==False and self.exists==True):
            self.name=self.author_exist()['author'].values[0]
            
        if self.name is not None:
            self.url_name=urllib.parse.quote(self.name)
            self.dbpedia_name=self.name.replace(' ','_')
            
            #avoid non-alpha characters
            regex = re.compile('[^a-zA-Z|_]')
            self.dbpedia_name=regex.sub('', self.dbpedia_name)
        #gc = client.GoodreadsClient(API_KEY, API_SEC)
        #gc.author(self.id)
    
        
     #create method to find id if only name is given   
    
    def author_exist(self):
        #Function to check if author exists in personal DB
        #check for list of IDs
        if self.list_bool:
            df=unique_authors[unique_authors['author_id'].isin(self.id)]
        else:
            df=unique_authors[unique_authors['author_id'].isin([self.id])]
            
        return df



    def goodreads_info(self):
        #clause for id arrays
        
        #Function for finding author information off goodreads
        #check what you want to return using radio button etc.
        URL="https://www.goodreads.com/author/show/"+str(self.id)+".xml?key="+API_KEY
        soup = BeautifulSoup(urlopen(URL),'xml') #find a way to only return part of this page??
        name_author=soup.author.find('name').string
        gender=soup.gender.string
        hometown=soup.hometown.string
        born_at=soup.born_at.string
        born_at=pd.to_datetime(born_at,errors='coerce')
        died_at=soup.died_at.string
        died_at=pd.to_datetime(died_at,errors='coerce')
        image_url=soup.image_url.string

        d={"author_name":name_author,
           "author_id":self.id,
           "gender_goodreads":gender,
           "hometown":hometown,
           "born_at":born_at,
           "died_at":died_at,
           "author_image_url":image_url}
        #pd.DataFrame(pd.Series(d)).T
        #returns dictionary
        return d
    
    def dbpedia_info(self):
        #Function for finding author information off dbpedia
        #break into functions
        try:
            req = requests.get('http://dbpedia.org/data/'+self.dbpedia_name+'.json').json()
            data = req['http://dbpedia.org/resource/'+self.dbpedia_name]
        except:
            data=None
        try:
            birth_date=data['http://dbpedia.org/ontology/birthDate'][0]['value'] #cut the hypertext url?
            birth_date=pd.to_datetime(birth_date,errors='coerce') #just take string and convert to date_time later?
        except:
            birth_date=None

        try:
            birth_place=data['http://dbpedia.org/ontology/birthPlace'][0]['value']
            birth_place=birth_place.split('/')[-1]
            birth_place=birth_place.replace('_',' ')
        except:
            birth_place=None

        try:
            death_date=data['http://dbpedia.org/ontology/deathDate'][0]['value']
            death_date=pd.to_datetime(death_date,errors='coerce')
        except:
            death_date=None
        try:
            death_place=data['http://dbpedia.org/ontology/deathPlace'][0]['value']
            death_place=death_place.split('/')[-1]
            death_place=death_place.replace('_',' ')
        except:
            death_place=None
        try:
            gender=data["http://xmlns.com/foaf/0.1/gender"][0]['value']
        except:
            gender=None

        d={"author_name":self.name,
           "author_id":self.id,
           "birth_date_dbpedia":birth_date,
           "birth_place_dbpedia":birth_place,
           "death_date_dbpedia":death_date,
           "death_place_dbpedia":death_place,
            "gender_dbpedia":gender}
        
        return d
    
    #google searches:
    #check master file before doing google searches
    
    def url_search(self, url):
        #urllib method:
        #req = Request(url, headers=headers)
        #page = urlopen(req)
        
        #requests method:
        req = requests.get(url,headers=headers)
        page = req.text
        soup = BeautifulSoup(page, 'html.parser')
        
        try:
            res = soup.find('div', attrs={'class':'_XWk'})
            return res.text
        
        except:
            return None
    
    def birth_date(self):
        #try clean dates etc.
        #url='http://www.google.com/search?q=what+is+cillian+murphys+date+of+birth%3F'
        url='http://www.google.com/search?q=what+is+'+self.url_name+'+%28writer%29+date+of+birth%3F&hl=en'
        return self.url_search(url)

    def birth_place(self):
        url='http://www.google.com/search?q=what+is+'+self.url_name+'+%28writer%29+place+of+birth%3F&hl=en'
        return self.url_search(url)
        
    def death_date(self):
        url='http://www.google.com/search?q=what+is+'+self.url_name+'+%28writer%29+date+of+death%3F&hl=en'
        return self.url_search(url)
    
    def death_place(self):
        url='http://www.google.com/search?q=what+is+'+self.url_name+'+%28writer%29+place+of+death%3F&hl=en'
        return self.url_search(url)
    
    def first_published(self,book):
        book=re.sub(' ', '+', book)
        #add author name to query?
        url='http://www.google.com/search?q=when+was+'+book+'+'+self.url_name+'first+published%3F&hl=en'
        return self.url_search(url)


# Geo Functions



def geo1(location):
    place=geolocator.geocode(location,addressdetails=True, timeout=100000)
    
    if place is None:
        return
    else:
        latitude=place.latitude
        longitude=place.longitude
        try:
            country=place.raw["address"]["country"]
        except:
            country=None
        try:
            country_code=place.raw["address"]["country_code"]
        except:
            country_code=None
        try:
            city=place.raw["address"]["city"] #throws error for Kabul
        except:
            city=None
        #state=place.raw["address"]["state"]
        d={"place":location,
            "latitude_geo1": latitude,
           "longitude_geo1": longitude,
           "country_geo1": country,
           "country_code_geo1": country_code,
           "city_geo1": city,
           #"state_geo1": state
          }
        return d




def geo2(location):
    #preference
    place=geolocator2.geocode(location, timeout=100000)
    if place is None:
        return
    else:
        latitude=place.latitude
        longitude=place.longitude
        try:
            raw=place.raw['address_components']
        except:
            raw=None
        try:
            #country=place.raw['address_components'][-1]['long_name'] #not exact
            country=[ d for d in raw if d['types'] == ['country', 'political']][0]['long_name']
        except:
            country=None
        try:
            #country_code=place.raw['address_components'][-1]['short_name'] #not exact
            country_code=[ d for d in raw if d['types'] == ['country', 'political']][0]['short_name']
        except:
            country_code=None
        try:
            #city=place.raw['address_components'][0]['long_name'] #not exact
            city=[ d for d in raw if d['types'] == ['locality', 'political']][0]['long_name']
        except:
            city=None
        #state=place.raw['address_components'][-2]['long_name']
        d={"place":location,
            "latitude_geo2": latitude,
           "longitude_geo2": longitude,
           "country_geo2": country,
           "country_code_geo2": country_code,
           "city_geo2": city,
           #"state_geo2": state
          }
        return d    

