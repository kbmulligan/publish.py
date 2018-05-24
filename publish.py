# publish.py
# Author: n1t0r
#
# publish.py updates a file of current activities based on a dictionary of hastags
# LICENSE: MIT

import datetime
import time
import sys
import os
import unittest

import twitter

# file open constants
READ_AND_WRITE = 'r+'
READ_ONLY = 'r'
WRITE_ONLY = 'w'
READ_AND_WRITE_NEW_TRUNC = 'w+'

CONTINUOUS = False

seconds = 60            # seconds per interval (default=60)
interval = 30           # seconds multiplier between tweet checks (default=30)

REACH_BACK = 15         # how many posts to go back
latest_tweet_id = 0     # most recent tweet

KEY_FILENAME = 'keys/keys.txt'
LATEST_TWEETS_FILENAME = 'latest_unprocessed_tweets.txt'
LATEST_TWEET_ID_FILENAME = 'latest_tweet_id.txt'
LOG_FILENAME = 'publish.log'

ACTIVITY_FILENAME = '../public_html/currently.txt'
BOOK_FILENAME = '../public_html/books.txt'


# the dict KEYS below are what the program is going to scan twitter for
# the dict VALUES below are what the program is going write to the text file 
act_pairs = {       '#reading':         'reading : ', 
                    '#memorizing':      'memorizing : ',
                    '#tryingout':       'trying out : ',
                    '#thankfulfor':     'thankful for : ',
                    '#learning':        'learning : ',
                    '#listening to':    'listening to : ',
                    '#researching':     'researching : '}

HASHTAGS = act_pairs.keys()

ACTIVITY_SEPARATOR = ' : '
BOOK_SEPARATOR = ' : '

# hashtag which indicates a book has been read
BOOK_COMPLETE_COMMAND = '#finished'
TITLE_AUTHOR_SEPARATOR = 'by'


class Book:
    
    def __init__(self, title, author, date_finished):
        self.author = author
        self.title = title
        self.date_finished = date_finished 

    

def get_activity_updates (posts, activities) :
    """ Scan posts for activity updates and return pairs that qualify in a tuple. 
    """
    print('Checking for activity updates...')

    updates = []

    print('Scanning {} most recent posts'.format(len(posts)))
    
    for post in posts:
        unicode_post = post.text.encode(errors='replace')
        for act in activities:
            if act in unicode_post:
                #print('...HAS ACTIVITY KEY...')
                #print(act)
                print(unicode_post)
                
                new_activity = unicode_post.split(act)[-1].strip()
                updates.append((act, new_activity))

    return tuple(updates)
    


def update_activities (activities, filename=ACTIVITY_FILENAME) :
    """ Given activities, update filename with new activity pairs.
    """
    print('Updating activities...')
    
    if activities:
        print('Activities updates not empty, so opening {} for read and write'.format(filename))

        file_content = []

        # read everything into file_content
        with open(filename, READ_ONLY) as f:
            file_content = f.readlines()

            # check each line for all activity keywords
            for i, line in enumerate(file_content):   
                for act in activities:
                    keyword, subject = act

                    # if the keyword is found, replace that line
                    if act_pairs[keyword] in file_content[i]:
                        print('Overwriting a current activity line!')
                        file_content[i] = '{}{}\n'.format(act_pairs[keyword], subject)
            
        # write it all back to the file 
        with open(filename, READ_AND_WRITE_NEW_TRUNC) as f:
            for line in file_content:
                f.write(line) 
                
    print('Activity updating complete!')

def get_book_updates (posts):
    """ Scan posts for book updates and return any qualifying pairs as tuples. 
    """
    print('Checking for finished books...')

    updates = []

    for post in posts:
        if BOOK_COMPLETE_COMMAND in post.text:
            
            book_info = post.text.encode(errors='replace').split(BOOK_COMPLETE_COMMAND)[-1]
            title_author = [x.strip() for x in book_info.strip().split(TITLE_AUTHOR_SEPARATOR)]
            # title, author = tuple(title_author)
 
            if len(title_author) > 1:
                (title, auth) = title_author
                updates.append((title, auth))
            else:
                updates.append((title_author, "various"))

    return tuple(updates)


def update_books (updates, filename=BOOK_FILENAME) :
    """ Append finished books from updates to filename (if not already present). 
    """ 
    print('Updating finished books...')
    
    if updates:
        print('Book updates not empty, so opening {} for read and write'.format(filename))

        all_books = []
        with open(filename, READ_ONLY) as f:
            # read file into all_books
            all_books = f.readlines() 

            # insert new additions at the beginning
            for update in updates:
                if (book_is_unique(all_books, update)): 
                    title, author = update
                    all_books.insert(0, '{1}{0}{2}{0}{3}'.format(BOOK_SEPARATOR, title, 
                                        author, datetime.date.today()))
                    #print('Would write to file here!')

        # write it all back to the file 
        with open(filename, READ_AND_WRITE_NEW_TRUNC) as f:
            for line in all_books:
                f.write(line) 

    print('Book updating complete!')

def book_is_unique (all_books, new_book):
    """ Returns True if new_book is not already in all_books.
    """
    new_book_title = new_book[0].lower()
    recorded_titles = [book.split(book_separator)[0].lower() for book in all_books]
    return new_book_title in recorded_titles

def keys_from_file (filename):
    keys = []
    try: 
        with open(filename) as keyfile:
            keys = [line.strip() for line in keyfile if line]

    except IOError:
        print("IOError: Error opening that key file. {}".format(filename))
        usage()

    if (len(keys) != 5):
        print('Wrong number of keys in file! Four(4) required! First line is user.')
        usage()

    # print keys[0], keys[1], keys[2], keys[3]

    return keys

def keys_from_args (args):

    if (len(args) == 6):
        consumer_key = args[2]
        consumer_sec = args[3]
        access_token_key = args[4]
        access_token_sec = args[5]
    else:
        usage()

    return user, consumer_key, consumer_sec, access_token_key, access_token_sec


def usage ():
    print(sys.argv[0], '<user> [consumer key] [consumer secret] [access token key] [access token secret]')
    print(sys.argv[0], '[KEY FILE]')
    sys.exit()
    return

def get_latest_tweet_id (tweets) :
    return max([tweet.id for tweet in tweets])

def get_keys_and_user ():
    """ This function retrieves access keys and username from system arguments, a specified file,
        or a default file.
    """
    
    if (len(sys.argv) == 6):
        user, consumer_key, consumer_sec, access_token_key, access_token_sec = keys_from_args(sys.argv)
    elif (len(sys.argv) == 2):
        user, consumer_key, consumer_sec, access_token_key, access_token_sec = keys_from_file(sys.argv[1])
    elif (len(sys.argv) == 1):
        user, consumer_key, consumer_sec, access_token_key, access_token_sec = keys_from_file(KEY_FILENAME)
    else:
        usage()

    return user, consumer_key, consumer_sec, access_token_key, access_token_sec  


def do_update (posts):

    activity_updates = get_activity_updates(posts, HASHTAGS)
    print('Activity updates: {}'.format(activity_updates))
    update_activities(activity_updates)

    new_books = get_book_updates(posts)
    print('Book updates: {}'.format(new_books))
    update_books(new_books)

    log("Last update run: " + time.asctime(time.gmtime()) + " GMT " )


def no_update():
    print("Nothing new...")
    log("Last checked: {}".format(time.asctime(time.gmtime())))


def log (info, filename=LOG_FILENAME) :
    """ Writes "info" string to filename. Uses append mode for opening file.""" 
    with open(filename, WRITE_ONLY) as log_file :
        log_file.write("{}\n".format(info))



if __name__ == '__main__':

    user, ck, cs, atk, ats = get_keys_and_user ()

    api = twitter.Api(ck, cs, atk, ats)

    # This section opens LATEST_TWEET_ID_FILENAME and checks the last saved tweet id.
    try:
        with open(LATEST_TWEET_ID_FILENAME, READ_ONLY) as tweet_file:
            first_line = tweet_file.readline().strip()
            if first_line:
                last_tweet_id = int(first_line)
            else:
                last_tweet_id = 0

    except IOError:
        try:
            with open(LATEST_TWEET_ID_FILENAME, READ_AND_WRITE_NEW_TRUNC) as tweet_file :
                last_tweet_id = 0
        except:
            print("Really can't open a file!")
            
    # check posts initially
    latest_posts = api.GetUserTimeline(screen_name=user, since_id=last_tweet_id)
    print("Retrieved {} posts.".format(len(latest_posts)))

    if latest_posts:
        latest_tweet_id = get_latest_tweet_id(latest_posts)
        do_update(latest_posts)
    else:
        latest_tweet_id = last_tweet_id
        no_update()

    with open(LATEST_TWEETS_FILENAME, READ_AND_WRITE) as tweet_file :
        for (content, tid) in [(post.text.encode(errors='replace'), post.id) for post in latest_posts] :
            tweet_file.write('{} : {}\n'.format(tid, content))

    print("Latest tweet id in file: {}".format(last_tweet_id))
    print("Latest tweet id just retrieved: {}".format(latest_tweet_id))

    with open(LATEST_TWEET_ID_FILENAME, READ_AND_WRITE) as tweet_file:
        tweet_file.write('{}\n'.format(latest_tweet_id))


    ### CONTINUOUS MODE ######################
    while CONTINUOUS:

        latest_posts = api.GetUserTimeline(screen_name=user, since_id=latest_tweet_id)

        if latest_posts:
            latest_tweet_id = get_latest_tweet_id(latest_posts)
            do_update(latest_posts)
        else:
            latest_tweet_id = last_tweet_id
            no_update()

        # wait
        time.sleep(seconds*interval)
    """ This function retrieves access keys and username from system arguments, a specified file,
        or a default file.
    """
