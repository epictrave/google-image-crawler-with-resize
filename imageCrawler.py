#!/usr/bin/env python
#-*- coding: UTF-8 -*-
#Searching and Downloading Google Images/Image Links
#Import Libraries
import time       #Importing the time library to check the time of code execution
import sys    #Importing the System Library
if sys.version_info[0] >= 3:
    unicode = str
import os
import os.path as osp
import fnmatch
import json
#import urllib2
import requests
from urllib.parse import urlencode
try:
    # For Python 3.0 and later
    from urllib.request import URLError, HTTPError, Request, urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import URLError, HTTPError, Request, urlopen
import datetime
import hashlib
from collections import OrderedDict

########### Default CONFIGS ###########
CONFIGS = {}

# How many images you want to download for each class. Google will only return 100 images at most for one search
CONFIGS[u'num_downloads_for_each_class'] = int(sys.argv[2])

# image type to search
#CONFIGS[u'search_file_type'] = 'jpg'
#CONFIGS[u'search_file_type'] = 'bmp'
CONFIGS[u'search_file_type'] = 'png'
CONFIGS[u'search_cdr_days'] = 100

CONFIGS[u'search_keywords_dict'] = {sys.argv[1]:[unicode(sys.argv[1])]}
CONFIGS[u'save_dir'] = './'
print('==>CONFIGS:')
print(CONFIGS)

if not osp.exists(CONFIGS[u'save_dir']):
    os.mkdir(CONFIGS[u'save_dir'])

########### End of CONFIGS ###########

########### Functions to Load downloaded urls ###########
def load_url_files(_dir, file_name_prefix):
    url_list = []
    ttl_url_list_file_name = osp.join(_dir, file_name_prefix +'_all.txt')
    if osp.exists(ttl_url_list_file_name):
        fp_urls = open(ttl_url_list_file_name, 'r')        #Open the text file called database.txt
        print('load URLs from file: ' + ttl_url_list_file_name)
        
        i = 0
        for line in fp_urls:
            line = line.strip()
            if len(line)>0:
                splits = line.split('\t')
                url_list.append(splits[0].strip())
                i=i+1
                
        print(str(i) + ' URLs loaded')
        fp_urls.close()             
    else:
        url_list = load_all_url_files(_dir, file_name_prefix)
            
    return url_list     

def load_all_url_files(_dir, file_name_prefix):
    url_list = []
    
    for file_name in os.listdir(_dir):
        if fnmatch.fnmatch(file_name, file_name_prefix +'*.txt'):
            file_name = osp.join(_dir, file_name)
            fp_urls = open(file_name, 'r')        #Open the text file called database.txt
            print('load URLs from file: ' + file_name)
            
            i = 0
            for line in fp_urls:
                line = line.strip()
                if len(line)>0:
                    splits = line.split('\t')
                    url_list.append(splits[0].strip())
                    i=i+1
            print(str(i) + ' URLs loaded')
            fp_urls.close()
            
    return url_list         
########### End of Functions to Load downloaded urls ###########

############## Functions to get date/time strings ############       

def get_current_date():
    tm = time.gmtime()
    date = datetime.date(tm.tm_year, tm.tm_mon, tm.tm_mday)   
    return date
    
def get_new_date_by_delta_days(date, delta_days):
    delta = datetime.timedelta(delta_days)
    new_date = date+delta
    return new_date
    
#Make a string from current GMT time
def get_gmttime_string():
    _str = time.strftime("GMT%Y%m%d_%H%M%S", time.gmtime())
    return _str
 
#Make a string from current local time
def get_localtime_string():
    _str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    return _str
############## End of Functions to get date/time strings ############          
    
############## Google Image Search functions ############    
# Get Image URL list form Google image search by keyword
def google_get_query_url(keyword, file_type, cdr):
    url = None
    
    # if keyword is unicode, we need to encode it into utf-8
    if isinstance(keyword, unicode):
        keyword = keyword.encode('utf-8')
        
    query = dict(q = keyword, 
                 tbm = 'isch',
                 tbs=cdr+',ift:'+file_type)
    
    #url = 'https://www.google.com/search?q=' + keyword + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
    #url = 'https://www.google.com/search?as_oq=' + keyword + '&as_st=y&tbm=isch&safe=images&tbs=ift:jpg'
    url = 'https://www.google.com/search?'+urlencode(query)
			
    print("\t==>Google Query URL is: " + url)
    return url
    
#Downloading entire Web Document (Raw Page Content)
def google_download_page(url):
    version = (3,0)
    cur_version = sys.version_info
    if cur_version >= version:     #If the Current Version of Python is 3.0 or above
        import urllib.request    #urllib library for Extracting web pages
        try:
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
            req = urllib.request.Request(url, headers = headers)
            resp = urllib.request.urlopen(req)
            respData = str(resp.read())
            return respData
        except Exception as e:
            print(str(e))
    else:                        #If the Current Version of Python is 2.x
        import urllib2.request
        try:
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
            req = urllib2.Request(url, headers = headers)
            response = urllib2.urlopen(req)
            page = response.read()
            return page
        except:
            return"Page Not found"

#Finding 'Next Image' from the given raw page
def google_images_get_next_item(s):
    start_line = s.find('rg_di')
    if start_line == -1:    #If no links are found then give an error!
        end_quote = 0
        link = "no_links"
        return link, end_quote
    else:
        start_line = s.find('"class="rg_meta"')
        start_content = s.find('"ou"',start_line+1)
        end_content = s.find(',"ow"',start_content+1)
        content_raw = str(s[start_content+6:end_content-1])
        return content_raw, end_content

#Getting all links with the help of '_images_get_next_image'
def google_images_get_all_items(page):
    items = []
    while True:
        item, end_content = google_images_get_next_item(page)
        if item == "no_links":
            break
        else:
            items.append(item)      #Append all the links in the list named 'Links'
            time.sleep(0.1)        #Timer could be used to slow down the request for image downloads
            page = page[end_content:]
    return items
   
def google_search_keyword(keyword, file_type, cdr):  
    query_url = google_get_query_url(keyword, file_type, cdr)
    raw_html =  (google_download_page(query_url))
    time.sleep(0.1)
    image_url_list = google_images_get_all_items(raw_html)    
    return image_url_list    
############## End of Google Image Search functions ############    
    
############## Functions to get real urls and download images ############       
#Get real url of a input url    
def get_real_url(url, loaded_urls):
    real_url = None
    response = None
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
        response = urlopen(req)
        
        real_url = response.geturl()
        print('Real_url is: ' + str(real_url))
        
        if real_url in loaded_urls:
            print('URL had been downloaded in previous ')
            real_url = None
        
    except IOError as e:   #If there is any IOError
        print("IOError on url "+str(url))
        print(e)
    except HTTPError as e:  #If there is any HTTPError
        print("HTTPError on url "+str(url))
        print(e)
    except URLError as e:
        print("URLError on url "+str(url))
        print(e)

    if response:
        response.close()    
        
    return real_url
def download_image(url, save_dir, loaded_urls=None):
    real_url = None
    response = None
    save_image_name = None
    global image_number
    global preimage_number
    image_number+=1
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
        response = urlopen(req)
        
        real_url = response.geturl()
        
        if loaded_urls and real_url in loaded_urls:
            print('URL had been downloaded in previous searching')
            image_number = preimage_number
            real_url = None
        else:
            img_name = str(time.time())[-10:]
            save_image_name = save_dir + '/' + img_name + '.' + CONFIGS[u'search_file_type']
            print('r save # '+ str(image_number)+ ' image\'s url: ' + real_url + '\ninto file: ' +  save_image_name)
            output_file = open(save_image_name,'wb')
            data = response.read()
            output_file.write(data)
        
        #response.close()
    except IOError as e:   #If there is any IOError
        print("IOError on url "+str(url))
        print(e)
        image_number = preimage_number
    except HTTPError as e:  #If there is any HTTPError
        print("HTTPError on url "+str(url))
        print(e)
        image_number = preimage_number
    except URLError as e:
        print("URLError on url "+str(url))
        print(e)
        image_number = preimage_number
    if response:
        response.close()

    return real_url, save_image_name
############## End of Functions to get real urls and download images ############         
def isNumber(s):
  try:
    int(s)
    return True
  except ValueError:
    return False
############## Main Program ############
if len(sys.argv) != 3:          
    print('Usage python imageCrawler.py [Keyword] [Number(int)]')
    exit(1)
elif not type(sys.argv[1]) is str : 
    print('Usage python imageCrawler.py [Keyword] [Number(int)]')
    exit(1)
elif not isNumber(sys.argv[2]):
    print('Usage python imageCrawler.py [Keyword] [Number(int)]')
    exit(1)

t0 = time.time()   #start the timer
folder_path = './' + sys.argv[1] + '/'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
file_list = os.listdir(folder_path)
print('files number: ' + str(len(file_list)))
image_number = preimage_number = len(file_list)
if image_number >= int(sys.argv[2]) :
    print("Existed Image number is " + sys.argv[2] + ' or more\nYou should Enter Bigger than '+ str(image_number))
    exit(1)


#Download Image Links
i= 0

cur_date = get_current_date()
print("Today is: " + cur_date.strftime("%Y/%m/%d"))

time_str = get_gmttime_string()

for class_name,search_keywords in CONFIGS[u'search_keywords_dict'].items():
    print( "Class no.: " + str(i+1) + " -->" + " Class name = " + str(class_name))
   
    class_urls_file_prefix = str(class_name).strip()
    
    items = load_url_files(CONFIGS[u'save_dir'], class_urls_file_prefix)    
    loaded_urls_num = len(items)
    print('Loaded URLs in total is: ', loaded_urls_num)

    # load pre-saved download parameters, actually cd_min for date range
    cd_max = cur_date

    params_file = osp.join(CONFIGS[u'save_dir'], class_urls_file_prefix + '_params' + '.txt')
    print( 'Loaded pre-saved download parameters from: ' + params_file)
    params_list = []
    fp_params = open(params_file, 'a+')
    for line in fp_params:
        line = line.strip()
        if line!='':
            params_list.append(line)
            print( "\t-->loaded parameters: ", line)
            
    if len(params_list)>0:
        splits = params_list[-1].split('/')
        if len(splits)==3:
            cd_max = datetime.date(int(splits[0]), int(splits[1]), int(splits[2]))
    
    cd_min = get_new_date_by_delta_days(cd_max, -CONFIGS[u'search_cdr_days'])   
    print( 'cd_max: ', cd_max)
    print( 'cd_min: ', cd_min)
            
    print ("Crawling Images...")
    
    class_save_dir = osp.join(CONFIGS[u'save_dir'], class_urls_file_prefix)
    if not osp.exists(class_save_dir):
        os.mkdir(class_save_dir)
    
    output_all_urls_file  = osp.join(CONFIGS[u'save_dir'], class_urls_file_prefix +'_all.txt')        
    fp_all_urls = open(output_all_urls_file, 'a+')
    
    output_urls_file = osp.join(CONFIGS[u'save_dir'], class_urls_file_prefix + '.txt')
    fp_urls = open(output_urls_file, 'a+')
    
#    if osp.exists(output_urls_file):
#        fp_urls = open(output_urls_file, 'a+')        #Open the text file called database.txt
#        for line in fp_urls:
#            items.append(line.strip())
#    else:
#        fp_urls = open(output_urls_file, 'w+')        #Open the text file called database.txt
#    
    cdr_enabled = False
    
    while True:        
        if cdr_enabled:
            cdr = 'cdr:1,cd_min:{},cd_max:{}'.format(cd_min.strftime('%m/%d/%Y'), cd_max.strftime('%m/%d/%Y'))
            print( "==>Search for Images between " + cd_min.strftime("%Y/%m/%d") + ' and ' + cd_max.strftime("%Y/%m/%d"))
        else:
            cdr = ''
            print( "==>Search for Images in any time")

        j = 0
                
        # Google only return 100 images at most for one search. So we may need to try many times
        while j<len(search_keywords):
            print( "\t==>Class name=" + str(class_name) + ', search keywords=' + search_keywords[j])
            keyword = search_keywords[j]#.replace(' ','%20')
            
#            # if keyword is unicode, we need to encode it into utf-8
#            if isinstance(keyword, unicode):
#                keyword = keyword.encode('utf-8')
            
#            query = dict(q = keyword, 
#                         tbm = 'isch',
#                         tbs=tbs+',ift:'+CONFIGS[u'search_file_type'])
#            
#            #url = 'https://www.google.com/search?q=' + keyword + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
#            #url = 'https://www.google.com/search?as_oq=' + keyword + '&as_st=y&tbm=isch&safe=images&tbs=ift:jpg'
#            url = 'https://www.google.com/search?'+urlencode(query)
#			
#            print "\t==>Query URL is: " + url
#			
#            raw_html =  (download_page(url))
#            time.sleep(0.1)
#            new_items = _images_get_all_items(raw_html)
            
            new_items = google_search_keyword(keyword, CONFIGS[u'search_file_type'], cdr)
           
            for url in new_items:
                #real_url = get_real_url(url)
                preimage_number = image_number
                real_url, save_name = download_image(url, class_save_dir, items)
                
                if image_number >= CONFIGS[u'num_downloads_for_each_class']:          
                    break
                if real_url and real_url not in items:
                    items.append(real_url)
                    fp_all_urls.write(real_url + '\t' + save_name + "\n")
                    fp_urls.write(real_url + '\t' + save_name + "\n")

            fp_all_urls.flush()                    
            fp_urls.flush()

            print( 'len(items)=', len(items))
            j = j + 1
        
        if cdr_enabled:
            fp_params.write('{}/{}/{}\n'.format( cd_min.year, cd_min.month, cd_min.day))
            cd_max = cd_min
            cd_min = get_new_date_by_delta_days(cd_max, -CONFIGS[u'search_cdr_days'])               
        else:
            fp_params.write('{}/{}/{}\n'.format( cd_max.year, cd_max.month, cd_max.day))
            cdr_enabled = True

        fp_params.flush()
        print( 'len(items)=', len(items))
        if image_number >= CONFIGS[u'num_downloads_for_each_class']:          
            break
        print('=======Wating=====')
    fp_params.close()
    fp_all_urls.close()
    fp_urls.close()

    #print ("Image Links = "+str(items))
    print ("Total New Image Links = " + str(len(items) - loaded_urls_num))
    print ("\n")
    i = i+1

    t1 = time.time()    #stop the timer
    total_time = t1-t0   #Calculating the total time required to crawl, find and download all the links of 60,000 images
    print('Total Saved Images number : '+ str(image_number))
    print("Total time taken: "+str(total_time)+" Seconds")

print("\n")
print("===All are downloaded")
#----End of the main program ----#