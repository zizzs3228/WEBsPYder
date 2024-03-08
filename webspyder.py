import argparse
from colorama import init, Fore
import requests
import threading
import time
import bs4
import json
import re
from tabulate import tabulate
from progress.spinner import Spinner
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')



parser = argparse.ArgumentParser()
parser.add_argument('-u','--URL', help='URL from site to scan. Example: -u http://example.com/admin', required=True, type=str)
parser.add_argument('-t','--threads', help='Number of threads to use. Example: -t 6', required=False, type=int, default=1)
parser.add_argument('-o','--output', help='Output file. Example: -o example', required=False, type=str, default='output')
parser.add_argument('-l','--level', help='Level of scan. 1 - only sitemap and robots.txt + crawler, 2 - FUZZING, 3 - FUZZING + crawler. Example: -l 3', required=False, type=int, default=3)
args = parser.parse_args()

URL = args.URL
threadnumber = args.threads
output = args.output
level = args.level


requests403 = []
internallinks = []
requests200 = []
URLtotest = [URL]
useragent = {'User-Agent':'GoogleBot','Connection':'close'}
startURL = URL.split('/')
if len(startURL) < 4:
    print('Whong URL format. Example: http://example.com/admin')
    parser.print_help()
startURL = '/'.join(startURL[:3])
sleeping = False
sitemaps = [startURL+'/sitemap.xml']
timeoutcounter = 0
bruteforceprogress = 0
state = 'NOT STARTED'


def split_array(arr, n):
    if n <= 0:
        print('n должно быть больше 0')
        return None
    if len(arr) < n:
        n = len(arr)
        quotient = 1
        remainder = 0
    else:
        quotient = len(arr) // n
        remainder = len(arr) % n
    result = []
    idx = 0
    for i in range(n):
        length = quotient + 1 if i < remainder else quotient
        result.append(arr[idx:idx + length])
        idx += length
    return result

def internalURLcheck(target:str)->bool:
    tempURL = URL.split('/')[2].split('.')
    if tempURL[0].isnumeric() and tempURL[1].isnumeric() and tempURL[2].isnumeric():
        tempURL = '.'.join(tempURL)
        if tempURL in target:
            return True
    else:
        tempURL = '.'.join(tempURL[-2:])
        if tempURL in target:
            return True
    return False

def crawler(level:int)->None:
    global state
    if level!=1 and level!=2 and level!=3:
        print('Неверный режим работы')
        return None
    if level==1 or level==3:
        def robotstxtparser(startURL:str)->None:
            global URLtotest
            global timeoutcounter
            global requests200
            global requests403
            global sitemaps
            global sleeping
            target = startURL+'/robots.txt'
            rqst = None
            try:
                rqst = requests.get(target, headers=useragent, timeout=5)
            except requests.ConnectionError as e:
                print(str(e))
                with threading.Lock():
                    sleeping = True
                time.sleep(30)
                with threading.Lock():
                    sleeping = False
                return None     
            except requests.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
                timeoutcounter+=1
                if timeoutcounter>5:
                    print('Слишком много таймаутов, выходим')
                    return None
                return None
            except requests.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
                return None
            except KeyboardInterrupt:
                print("Someone closed the program")
            if rqst!=None:
                if rqst.status_code == 200:
                    print(Fore.GREEN+f'[+] {target} '+'found'+Fore.RESET)
                    lines = rqst.text.splitlines()
                    for line in lines:
                        if 'Disallow' in line:
                            line = line.split(':')[1:]
                            line = ''.join(line).strip()
                            if line != '/':
                                if line != '*':
                                    if line != '/*':
                                        if line != '':
                                            if line != '/ ':
                                                if line != '/* ':
                                                    if line != ' ':
                                                        if '=' in line or '?' in line or '$' in line:
                                                            continue
                                                        temp = line.split('/')
                                                        con = False
                                                        for t in temp:
                                                            if t!='*' and '*' in t:
                                                                con = True
                                                                break
                                                        if line.count('*')>1:
                                                            con = True
                                                        if '*' in line[:-3]:
                                                            con = True
                                                        if con:
                                                            continue
                                                        line = '/'.join(temp)
                                                        if line[-1]=='/':
                                                            if line[:-1] not in URLtotest:
                                                                URLtotest.append(startURL+line[:-1])
                                                        else:
                                                            if line not in URLtotest:
                                                                URLtotest.append(startURL+line)
                        if 'Allow' in line:
                            line = line.split(':')[1:]
                            line = ''.join(line).strip()
                            if line != '/':
                                if line != '*':
                                    if line != '/*':
                                        if line != '':
                                            if line != '/ ':
                                                if line != '/* ':
                                                    if line != ' ':
                                                        if '=' in line or '?' in line or '$' in line:
                                                            continue
                                                        temp = line.split('/')
                                                        con = False
                                                        for t in temp:
                                                            if t!='*' and '*' in t:
                                                                con = True
                                                                break
                                                        if line.count('*')>1:
                                                            con = True
                                                        if '*' in line[:-3]:
                                                            con = True
                                                        if con:
                                                            continue
                                                        line = '/'.join(temp)
                                                        if line[-1]=='/':
                                                            if line[:-1] not in URLtotest:
                                                                URLtotest.append(line[:-1])
                                                        else:
                                                            if line not in URLtotest:
                                                                URLtotest.append(line)
                        if 'Sitemap' in line:
                            line = line.split(':')[1:]
                            line = ':'.join(line).strip()
                            if line != '/':
                                if line != '*':
                                    if line != '/*':
                                        if line != '':
                                            if line != '/ ':
                                                if line != '/* ':
                                                    if line != ' ':
                                                        if line not in sitemaps and line[-4:] == '.xml':
                                                            sitemaps.append(line)
                elif rqst.status_code == 403:
                    print(Fore.LIGHTRED_EX+f'[+] {target} '+'found, but access denied(403)'+Fore.RESET)
                    if target not in requests403:
                        requests403.append(target)
                else:
                    print(Fore.RED+f'[+] {target} '+'not found'+Fore.RESET)
        robotstxtparser(startURL)

        def xmlrecursive(target:str)->None:
            global timeoutcounter
            global requests200
            global requests403
            global sleeping
            threads = []
            rqst = None
            try:
                rqst = requests.get(target, headers=useragent, timeout=5)
            except requests.ConnectionError as e:
                print(str(e))
                with threading.Lock():
                    sleeping = True
                time.sleep(30)
                with threading.Lock():
                    sleeping = False
                return None     
            except requests.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
                timeoutcounter+=1
                if timeoutcounter>5:
                    print('Слишком много таймаутов, выходим')
                    return None
                return None
            except requests.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
                return None
            except KeyboardInterrupt:
                print("Someone closed the program")
            if rqst!=None:
                if rqst.status_code == 200:
                    print(Fore.GREEN+f'[+] {target} '+'found'+Fore.RESET)
                    text = rqst.text
                    soup = bs4.BeautifulSoup(text,'lxml')
                    locs = soup.find_all('loc')
                    for loc in locs:
                        if sleeping:
                            time.sleep(10)
                        if 'http' in loc.text:
                            if loc.text[-4:]=='.xml':
                                t = threading.Thread(target=xmlrecursive, args=(loc.text,))
                                with threading.Lock():
                                    threads.append(t)
                                t.start()
                            else:
                                if loc.text[-1]=='/':
                                    if loc.text[:-1] not in URLtotest:
                                        with threading.Lock():
                                            URLtotest.append(loc.text[:-1])
                                else:
                                    if loc.text not in URLtotest:
                                        with threading.Lock():
                                            URLtotest.append(loc.text)
                    for thread in threads:
                        thread.join()
                            
                elif rqst.status_code == 403:
                    if target not in requests403:
                        print(Fore.LIGHTRED_EX+f'[+] {target} '+'found, but access denied(403)'+Fore.RESET)
                        with threading.Lock():
                            requests403.append(target)
                elif rqst.status_code == 429:
                    print('Слишком много запросов, спим')
                    sleeping = True
                    time.sleep(10)
                    sleeping = False
                else:
                    print(Fore.RED+f'[+] {target} '+'not found'+Fore.RESET)

        for site in sitemaps:
            xmlrecursive(site)

    if level==2 or level==3:
        global alldirectories
        global directories
        global timeoutcounter
        alldirectories = []
        directories = []
        timeoutcounter = 0
        print('\n\n[+] FUZZING started...')

        def recursivebrute(URL:str)->None:
            with open('URLenum.txt','r') as f:
                URLs = [x.strip() for x in f.readlines()]
            phps = [x+'.php' for x in URLs if '.' not in x and x[-1]!='/' and x[-4:]!='.php']
            slashes = [x+'/' for x in URLs if '.' not in x and x[-1]!='/' and x[-4:]!='.php']
            URLs = URLs+phps+slashes
            URLs = [startURL+'/'+x for x in URLs if x[0]!='/']
            def headcheck(URLs:list)->None:
                global URLtotest
                global timeoutcounter
                global requests403
                global sleeping
                global directories
                global bruteforceprogress
                for U in URLs:
                    with threading.Lock():
                        bruteforceprogress+=1
                    rqst = None
                    try:
                        rqst = requests.get(U, headers=useragent,timeout=10,allow_redirects=False)
                        rqst.close()
                    except requests.ConnectionError as e:
                        print(str(e))
                        with threading.Lock():
                            sleeping = True
                        time.sleep(30)
                        with threading.Lock():
                            sleeping = False
                        return None     
                    except requests.Timeout as e:
                        print("OOPS!! Timeout Error")
                        print(str(e))
                        timeoutcounter+=1
                        if timeoutcounter>5:
                            print('Слишком много таймаутов, выходим')
                            return None
                        return None
                    except requests.RequestException as e:
                        print("OOPS!! General Error")
                        print(str(e))
                        return None
                    except KeyboardInterrupt:
                        print("Someone closed the program")
                        
                    if rqst!=None:
                        if rqst.status_code == 200:
                            if '.' not in U.split('/')[-1]:
                                directories.append(U)
                            if U not in URLtotest:
                                with threading.Lock():
                                    URLtotest.append(U)
                            if U not in requests200:
                                with threading.Lock():
                                    requests200.append(U)
                            if U not in internallinks:
                                with threading.Lock():
                                    internallinks.append(U)
                        if rqst.status_code == 403:
                            if U not in requests403:
                                with threading.Lock():
                                    requests403.append(U)
                        if rqst.status_code == 429:
                            print('Слишком много запросов, спим')
                            with threading.Lock():
                                sleeping = True
                            time.sleep(10)
                            with threading.Lock():
                                sleeping = False
                return None
            splited = split_array(URLs,threadnumber)
            threads = []
            for spl in splited:
                t = threading.Thread(target=headcheck, args=(spl,))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()

        recursivebrute(startURL)
        alldirectories = directories.copy()
        directories = []
        # for dir in alldirectories:
        #     recursivebrute(dir)
        time.sleep(0.3)
        

    if level==1 or level==3:
        print('\n\n[+] Crawling started...')
        state = 'RUNNING'
        def pageparser(target:str)->None:
            global requests200
            global requests403
            global sleeping
            global timeoutcounter
            global internallinks
            starttarget = target
            startURL = target.split('/')
            startURL = '/'.join(startURL[:3])
            if sleeping:
                time.sleep(10)
            rqst = None
            try:
                rqst = requests.get(target, headers=useragent, timeout=5)
            except requests.ConnectionError as e:
                print(str(e))
                with threading.Lock():
                    sleeping = True
                time.sleep(30)
                with threading.Lock():
                    sleeping = False
                return None     
            except requests.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
                timeoutcounter+=1
                if timeoutcounter>5:
                    print('Слишком много таймаутов, выходим')
                    return None
                return None
            except requests.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
                return None
            except KeyboardInterrupt:
                print("Someone closed the program")
                with threading.Lock():
                    timeoutcounter+=1
                if timeoutcounter>5:
                    print('Слишком много таймаутов, выходим')
                    return None
            if rqst!=None:
                if rqst.status_code == 200:
                    soup = bs4.BeautifulSoup(rqst.text,'lxml')
                    alllinks = []
                    alllinks = alllinks+[link.get('href') for link in soup.find_all('a') if link.get('href') is not None and link.get('href')!='#' and link.get('href')!='' and link.get('href')!='/']
                    alllinks = alllinks+[link.get('action') for link in soup.find_all('form') if link.get('action') is not None and link.get('action')!='#' and link.get('action')!='' and link.get('action')!='/']
                    alllinks = alllinks+[link.get('href') for link in soup.find_all('link') if link.get('href') is not None and link.get('href')!='#' and link.get('href')!='' and link.get('href')!='/']
                    alllinks = alllinks+[link.get('src') for link in soup.find_all('script') if link.get('src') is not None and link.get('src')!='#' and link.get('src')!='' and link.get('src')!='/']
                    alllinks = alllinks+[link.get('src') for link in soup.find_all('iframe') if link.get('src') is not None and link.get('src')!='#' and link.get('src')!='' and link.get('src')!='/']
                    alllinks = list(set(alllinks))
                    goodlinks = []
                    if '.' in target.split('/')[-1]:
                        target = '/'.join(target.split('/')[:-1])
                    if target[-1]=='/':
                        target = target[:-1]
                    if alllinks!=[]:
                        for i in alllinks:
                            if '{' in i or '}' in i or ('tel' in i and '+' in i) or ('mailto' in i and '@' in i) or ('?' in i and '=' in i) or ('#' in i and '=' in i):
                                continue
                            if 'http' not in i:
                                if i.count('..')>1:
                                    continue
                                if i[:2]=='//':
                                    goodlinks.append('https:'+i)
                                elif i[0]=='/' and i[1]!='/':
                                    goodlinks.append(startURL+i)
                                elif i[0]=='.' and i[1]=='/':
                                    goodlinks.append(target+i[1:])
                                elif i[0]=='.' and i[1]=='.' and i[2]=='/':
                                    tmp = target.split('/')
                                    tmp = '/'.join(tmp[:-1])
                                    goodlinks.append(tmp+i[2:])
                                elif i[0]!='.' and i[0]!='/' and i[0]!='#' and '@' not in i and ':' not in i and '{' not in i and '}' not in i:
                                    goodlinks.append(target+'/'+i)
                            else:
                                goodlinks.append(i)
                        alllinks = goodlinks
                        alllinks = [x for x in alllinks if internalURLcheck(x)]
                        alllinks = [x for x in alllinks if x not in internallinks]
                        with threading.Lock():
                            internallinks = internallinks+alllinks+[starttarget]
                        URLparsing(alllinks)


                    if target not in requests200:
                        with threading.Lock():
                            requests200.append(starttarget)
                if rqst.status_code == 403:
                    if target not in requests403:
                        with threading.Lock():
                            requests403.append(starttarget)
                if rqst.status_code == 429:
                    print('Слишком много запросов, спим')
                    sleeping = True
                    time.sleep(10)
                    sleeping = False

        def jsparser(target:str)->None:
            global requests200
            global requests403
            global sleeping
            global timeoutcounter
            global internallinks
            starttarget = target
            startURL = target.split('/')
            startURL = '/'.join(startURL[:3])
            if sleeping:
                time.sleep(10)
            rqst = None
            try:
                rqst = requests.get(target, headers=useragent, timeout=5)
            except requests.ConnectionError as e:
                print(str(e))
                with threading.Lock():
                    sleeping = True
                time.sleep(30)
                with threading.Lock():
                    sleeping = False
                return None     
            except requests.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
                timeoutcounter+=1
                if timeoutcounter>5:
                    print('Слишком много таймаутов, выходим')
                    return None
                return None
            except requests.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
                return None
            except KeyboardInterrupt:
                print("Someone closed the program")
                with threading.Lock():
                    timeoutcounter+=1
                if timeoutcounter>5:
                    print('Слишком много таймаутов, выходим')
                    return None
            if rqst!=None:
                if rqst.status_code == 200:
                    js_data = rqst.text.split(';')
                    regular = r'href:\"\/.*?\"'
                    alllinks = re.findall(regular,rqst.text)
                    alllinks = [x[6:-1] for x in alllinks if x[6:-1]!='#' and x[6:-1]!='' and x[6:-1] is not None and x[6:-1]!='/' and x[6:-1] not in alllinks]
                    for line in js_data:
                        if any(['http://' in line, 'https://' in line]):
                            found = re.findall(r'\"(http[s]?://.*?)\"', line)
                            for item in found:
                                if len(item) > 8:
                                    if item is not None and item != '' and item != '#' and item != '/' and item not in alllinks:                               
                                        alllinks.append(item)
                    goodlinks = []
                    alllinks = list(set(alllinks))
                    if '.' in target.split('/')[-1]:
                        target = '/'.join(target.split('/')[:-1])
                    if target[-1]=='/':
                        target = target[:-1]
                    if alllinks!=[]:
                        for i in alllinks:
                            if '{' in i or '}' in i or ('tel' in i and '+' in i) or ('mailto' in i and '@' in i) or ('?' in i and '=' in i) or ('#' in i and '=' in i):
                                continue
                            if 'http' not in i:
                                if i.count('..')>1:
                                    continue
                                if i[:2]=='//':
                                    goodlinks.append('https:'+i)
                                elif i[0]=='/' and i[1]!='/':
                                    goodlinks.append(startURL+i)
                                elif i[0]=='.' and i[1]=='/':
                                    goodlinks.append(target+i[1:])
                                elif i[0]=='.' and i[1]=='.' and i[2]=='/':
                                    tmp = target.split('/')
                                    tmp = '/'.join(tmp[:-1])
                                    goodlinks.append(tmp+i[2:])
                                elif i[0]!='.' and i[0]!='/' and i[0]!='#' and '@' not in i and ':' not in i and '{' not in i and '}' not in i:
                                    goodlinks.append(target+'/'+i)
                            else:
                                goodlinks.append(i)
                        alllinks = goodlinks
                        alllinks = [x for x in alllinks if internalURLcheck(x)]
                        alllinks = [x for x in alllinks if x not in internallinks]
                        with threading.Lock():
                            internallinks = internallinks+alllinks+[starttarget]
                        URLparsing(alllinks)


                    if target not in requests200:
                        with threading.Lock():
                            requests200.append(starttarget)
                if rqst.status_code == 403:
                    if target not in requests403:
                        with threading.Lock():
                            requests403.append(starttarget)
                if rqst.status_code == 429:
                    print('Слишком много запросов, спим')
                    sleeping = True
                    time.sleep(10)
                    sleeping = False

        def cssparser(target:str)->None:
            global requests200
            global requests403
            global sleeping
            global timeoutcounter
            global internallinks
            starttarget = target
            startURL = target.split('/')
            startURL = '/'.join(startURL[:3])
            if sleeping:
                time.sleep(10)
            rqst = None
            try:
                rqst = requests.get(target, headers=useragent, timeout=5)
            except requests.ConnectionError as e:
                print(str(e))
                with threading.Lock():
                    sleeping = True
                time.sleep(30)
                with threading.Lock():
                    sleeping = False
                return None     
            except requests.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
                timeoutcounter+=1
                if timeoutcounter>5:
                    print('Слишком много таймаутов, выходим')
                    return None
                return None
            except requests.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
                return None
            except KeyboardInterrupt:
                print("Someone closed the program")
                with threading.Lock():
                    timeoutcounter+=1
                if timeoutcounter>5:
                    print('Слишком много таймаутов, выходим')
                    return None
            if rqst!=None:
                if rqst.status_code == 200:
                    regular = r"url\(\".*?\"\)"
                    alllinks = re.findall(regular,rqst.text)
                    alllinks = [x[5:-2] for x in alllinks if x[5:-2]!='#' and x[5:-2]!='' and x[5:-2] is not None and x[5:-2]!='/' and x[5:-2] not in alllinks]
                    goodlinks = []
                    alllinks = list(set(alllinks))
                    if '.' in target.split('/')[-1]:
                        target = '/'.join(target.split('/')[:-1])
                    if target[-1]=='/':
                        target = target[:-1]
                    if alllinks!=[]:
                        for i in alllinks:
                            if '{' in i or '}' in i or ('tel' in i and '+' in i) or ('mailto' in i and '@' in i) or ('?' in i and '=' in i) or ('#' in i and '=' in i):
                                continue
                            if 'http' not in i:
                                if i.count('..')>1:
                                    continue
                                if i[:2]=='//':
                                    goodlinks.append('https:'+i)
                                elif i[0]=='/' and i[1]!='/':
                                    goodlinks.append(startURL+i)
                                elif i[0]=='.' and i[1]=='/':
                                    goodlinks.append(target+i[1:])
                                elif i[0]=='.' and i[1]=='.' and i[2]=='/':
                                    tmp = target.split('/')
                                    tmp = '/'.join(tmp[:-1])
                                    goodlinks.append(tmp+i[2:])
                                elif i[0]!='.' and i[0]!='/' and i[0]!='#' and '@' not in i and ':' not in i and '{' not in i and '}' not in i:
                                    goodlinks.append(target+'/'+i)
                            else:
                                goodlinks.append(i)
                        alllinks = goodlinks
                        alllinks = [x for x in alllinks if internalURLcheck(x)]
                        alllinks = [x for x in alllinks if x not in internallinks]
                        with threading.Lock():
                            internallinks = internallinks+alllinks+[starttarget]
                        URLparsing(alllinks)

                    if target not in requests200:
                        with threading.Lock():
                            requests200.append(starttarget)
                if rqst.status_code == 403:
                    if target not in requests403:
                        with threading.Lock():
                            requests403.append(starttarget)
                if rqst.status_code == 429:
                    print('Слишком много запросов, спим')
                    sleeping = True
                    time.sleep(10)
                    sleeping = False

        def URLparsing(URLs:list)->None:
            for target in URLs:
                if target[-4:] == '.php':
                    pageparser(target)
                elif target[-5:] == '.html':
                    pageparser(target)
                elif '.' not in target.split('/')[-1]:
                    pageparser(target)
                elif target[-3:] == '.js':
                    jsparser(target)
                elif target[-4:] == '.css':
                    cssparser(target)

        splited = split_array(URLtotest,threadnumber)
        threads = []
        for spl in splited:
            t = threading.Thread(target=URLparsing, args=(spl,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        
        state = 'FINISHED'
        


if __name__ == '__main__':
    init()
    program_name = r'''
 __          ________ ____      _______     __ _           
 \ \        / /  ____|  _ \    |  __ \ \   / /| |          
  \ \  /\  / /| |__  | |_) |___| |__) \ \_/ /_| | ___ _ __ 
   \ \/  \/ / |  __| |  _ </ __|  ___/ \   / _` |/ _ \ '__|
    \  /\  /  | |____| |_) \__ \ |      | | (_| |  __/ |   
     \/  \/   |______|____/|___/_|      |_|\__,_|\___|_|                                              
'''
    author = r'''
  _           ________ ______________  
 | |__  _   _|__  /_ _|__  /__  / ___| 
 | '_ \| | | | / / | |  / /  / /\___ \ 
 | |_) | |_| |/ /_ | | / /_ / /_ ___) |
 |_.__/ \__, /____|___/____/____|____/ 
        |___/                                    
'''
    print(Fore.LIGHTCYAN_EX + program_name,Fore.LIGHTGREEN_EX + author+Fore.RESET)

    crawlerthread = threading.Thread(target=crawler, args=(level,))
    crawlerthread.daemon = True
    crawlerthread.start()
    
    if level == 2 or level == 3:
        while bruteforceprogress==0:
            time.sleep(1)
        max_iterations = 0
        with open('URLenum.txt','r') as f:
            tempURLS = [x.strip() for x in f.readlines()]
            tempPHPS = [x+'.php' for x in tempURLS if '.' not in x and x[-1]!='/' and x[-4:]!='.php']
            tempslashes = [x+'/' for x in tempURLS if '.' not in x and x[-1]!='/' and x[-4:]!='.php']
            tempURLS = tempURLS+tempPHPS+tempslashes
            tempURLS = [startURL+'/'+x for x in tempURLS if x[0]!='/']
            max_iterations = len(tempURLS)
        progress_bar = tqdm(total=max_iterations, desc='Scanning', unit='page(s)')
        while bruteforceprogress < max_iterations:
            progress_bar.update(bruteforceprogress - progress_bar.n)
            time.sleep(0.1)  # Пауза, чтобы не загружать процессор
        progress_bar.close()
        print(Fore.GREEN+'[+] FUZZING finished'+Fore.RESET)


    if level == 1 or level == 3:
        while state == 'NOT STARTED':
            time.sleep(0.1)
        spinner = Spinner('Crawling... ')
        while state != 'FINISHED':
            spinner.next()
        print('\n'+Fore.GREEN+'[+] Crawling finished'+Fore.RESET)
    
    crawlerthread.join()

    requests200 = list(set(requests200))
    requests403 = list(set(requests403))
    internallinks = list(set(internallinks))

    pages = []
    for link in internallinks:
        if '.' not in link.split('/')[-1]:
            pages.append(link)
        elif link[-4:] == '.php':
            pages.append(link)
        elif link[-5:] == '.html':
            pages.append(link)

    files = []
    for link in internallinks:
        if '.' in link.split('/')[-1]:
            if link[-4:] != '.php' and link[-5:] != '.html':
                files.append(link)

    

    # Создание списка списков для tabulate
    data = {
        f'pages({len(pages)})': pages,
        f'requests403({len(requests403)})': requests403,
        f'requests200({len(requests200)})': requests200
    }

    # Вывод массивов по столбикам в терминале
    print('\n\n')
    print(tabulate(data, headers="keys",stralign="left",tablefmt="fancy_grid",colalign=("center","center","center")))

    docxfiles = [x for x in files if x[-5:] == '.docx']
    pdfs = [x for x in files if x[-4:] == '.pdf']
    xlsxs = [x for x in files if x[-5:] == '.xlsx']
    if docxfiles != [] or pdfs != [] or xlsxs != []:
        data2 = {
            f'docx({len(docxfiles)})': docxfiles,
            f'pdf({len(pdfs)})': pdfs,
            f'xlsx({len(xlsxs)})': xlsxs
        }

        print('\n\n')
        print(tabulate(data2, headers="keys",stralign="left",tablefmt="fancy_grid",colalign=("center","center","center")))

    pictures = []
    otherfiles = []
    for file in files:
        if file[-5:] != '.docx' and file[-4:] != '.pdf' and file[-5:] != '.xlsx':
            if file[-4:] == '.jpg' or file[-4:] == '.png' or file[-4:] == '.gif' or file[-4:] == '.svg' or file[-4:] == '.bmp' or file[-4:] == '.ico':
                pictures.append(file)
            else:
                otherfiles.append(file)
    
    if pictures != [] or otherfiles != []:
        data3 = {
            f'pictures({len(pictures)})': pictures,
            f'other files({len(otherfiles)})': otherfiles
        }

        print('\n\n')
        print(tabulate(data3, headers="keys",stralign="left",tablefmt="fancy_grid",colalign=("center","center")))

    print('\n')
    with open(output+'.txt','w') as f:
        if pages != []:
            f.write('Pages:\n')
            for page in pages:
                f.write(page+'\n')
            f.write('\n')
        if requests403 != []:
            f.write('403:\n')
            for req in requests403:
                f.write(req+'\n')
            f.write('\n')
        if requests200 != []:
            f.write('200:\n')
            for req in requests200:
                f.write(req+'\n')
            f.write('\n')
        if docxfiles != []:
            f.write('Docx:\n')
            for docx in docxfiles:
                f.write(docx+'\n')
            f.write('\n')
        if pdfs != []:
            f.write('PDF:\n')
            for pdf in pdfs:
                f.write(pdf+'\n')
            f.write('\n')
        if xlsxs != []:
            f.write('XLSX:\n')
            for xlsx in xlsxs:
                f.write(xlsx+'\n')
            f.write('\n')
        if pictures != []:
            f.write('Pictures:\n')
            for pic in pictures:
                f.write(pic+'\n')
            f.write('\n')
        if otherfiles != []:
            f.write('Other files:\n')
            for other in otherfiles:
                f.write(other+'\n')
            f.write('\n')

    print(Fore.BLUE+f'[+] Output saved to {output+".txt"}'+Fore.RESET)

    data = {}

    if pages != []:
        data['Pages'] = pages
    if requests403 != []:
        data['403'] = requests403
    if requests200 != []:
        data['200'] = requests200
    if docxfiles != []:
        data['Docx'] = docxfiles
    if pdfs != []:
        data['PDF'] = pdfs
    if xlsxs != []:
        data['XLSX'] = xlsxs
    if pictures != []:
        data['Pictures'] = pictures
    if otherfiles != []:
        data['Other files'] = otherfiles

    # Сохранение данных в JSON-файл
    with open(output+'.json', 'w') as f:
        json.dump(data, f, indent=4)

    print(Fore.BLUE + f'[+] Json saved to {output+".json"}' + Fore.RESET)

    # print(internallinks,'\n\n',requests200,'\n\n',requests403,'\n\n',URLtotest,'\n\n',sitemaps)

    

