# publish.py
# Author: n1t0r
#
# publish.py updates a file of current activities based on a dictionary of hastags
# LICENSE: MIT

import datetime
import time
import sys
import os
import pprint
# import csv

import twitter

# file open constants
READ_AND_WRITE = 'r+'
READ_ONLY = 'r'
WRITE_ONLY = 'w'
READ_AND_WRITE_NEW_TRUNC = 'w+'
APPEND = 'a'

CONTINUOUS = False
VERBOSE = False

COMPATIBILITY = 'compat'
EXTENDED = 'extended'
TWEET_MODE = EXTENDED 

REACH_BACK = 15                     # how many posts to go back

KEY_FILENAME = 'keys/keys.txt'
LATEST_TWEETS_FILENAME = 'latest_tweets.txt'
LAST_TWEET_ID_FILENAME = 'last_tweet_id.txt'
LOG_FILENAME = 'publish.log'


# database files
ACTIVITY_FILENAME = '../public_html/currently.txt'
BOOK_FILENAME = '../public_html/books.txt'

# the dict KEYS below are what the program is going to scan twitter for
# the dict VALUES below are what the program is going write to the text file 
act_pairs = {        '#reading':         'reading', 
                     '#memorizing':      'memorizing',
                     '#tryingout':       'trying out',
                     '#thankfulfor':     'thankful for',
                     '#learning':        'learning',
                     '#listening to':    'listening to',
                     '#researching':     'researching'}

HASHTAGS = act_pairs.keys()

# FORMATTING
ACTIVITY_SEPARATOR = ';'
BOOK_SEPARATOR = ';'
STRIP_CHARS = '!?. '

# hashtag which indicates a book has been read
BOOK_COMPLETE_COMMAND = '#finished'
TITLE_AUTHOR_SEPARATOR = ' by '


class Act:

    def __init__(self, label, subject, started=None, ended=None):
        self.label = label
        self.subject = subject
        self.started = datetime.datetime.now() 
        self.hashtag = '#' + ''.join(label.split())

    def __repr__(self):
        return "{}: {} {}".format(hashtag, label, subject)

    def end():
        self.ended = datetime.datetime.now() 

    def get_label():
        return self.label

    def get_subject():
        return self.subject

    def get_hashtag():
        return self.hastag


class Book:
    
    def __init__(self, title, author, date_finished=None):
        self.author = author
        self.title = title
        self.date_finished = date_finished 


    def as_tuple(self):
        return (self.title, self.author, self.date_finished)
    
    def __repr__(self):
        return "{} by {}".format(self.title, self.author)

    def __eq__(self, other):
        return self.title == other.title and self.author == other.author

    def __ne__(self, other):
        return not self.__eq__(other)


def extract_full_text(tweet):
    """ Returns the full text of a tweet. Checks for truncation. """

    if tweet.tweet_mode == EXTENDED:
        full_text = tweet.full_text
    else:
        full_text = tweet.text
    return convert(full_text)

def convert(unicode_text):
    return unicode_text.encode(errors='replace')

def get_activity_updates (posts, activities) :
    """ Scan posts for activity updates and return pairs that qualify in a tuple. """

    print('Checking for activity updates...')
    print('Scanning {} most recent posts'.format(len(posts)))
    
    updates = []
    for post in posts:

        for hashtag in activities:
            if hashtag in post:
                print(post)  
                
                # split string at 'act' and take end element
                new_activity = post.split(hashtag)[-1].strip().strip(STRIP_CHARS)
                updates.append((hashtag, new_activity))

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
                for keyword, subject in activities:
                    # if the keyword is found, replace that line
                    if act_pairs[keyword] == file_content[i].split(ACTIVITY_SEPARATOR)[0]:
                        print('Overwriting a current activity line!')
                        file_content[i] = '{}{}{}\n'.format(
                                            act_pairs[keyword], ACTIVITY_SEPARATOR, subject)
            
        # write it all back to the file 
        with open(filename, READ_AND_WRITE_NEW_TRUNC) as f:
            for line in file_content:
                f.write(line) 
                
    print('Activity updating complete!')


def get_book_updates (posts):
    """ Scan posts for book updates and return any qualifying pairs as tuples. 
    """
    print('Checking for finished books...')
    print('Scanning {} most recent posts'.format(len(posts)))

    updates = []
    for post in posts:
        if BOOK_COMPLETE_COMMAND in post:
            book = extract_book_from_string(post)
            updates.append(book.as_tuple())

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
                    title, author, _ = update
                    all_books.insert(0, '{1}{0}{2}{0}{3}\n'.format(BOOK_SEPARATOR, title, 
                                        author, datetime.date.today()))
                    #print('Would write to file here!')

        # write it all back to the file 
        with open(filename, READ_AND_WRITE_NEW_TRUNC) as f:
            for line in all_books:
                f.write(line) 

    print('Book updating complete!')

def extract_book_from_string(text):
    
    # Break tweet at BOOK_COMPLETE_COMMAND and take everything afterward
    book_info = text.encode(errors='replace').split(BOOK_COMPLETE_COMMAND)[-1]

    book_info_and_link = book_info.split("http://")

    prefixes = ['http://', 'https://']
    if any(prefix in book_info for prefix in prefixes):
        for prefix in prefixes:
            book_info = book_info.split(prefix)[0] 

    # Remove trailing whitespace and split at TITLE_AUTHOR_SEPARATOR
    title_and_author = [x.strip().strip(STRIP_CHARS) for x in book_info.strip().split(TITLE_AUTHOR_SEPARATOR)]

    title = title_and_author[0]                  # first bit 
    author = "".join(title_and_author[1:])       # the rest of it

    return Book(title, author) 

def book_is_unique (all_books, new_book):
    """ Returns True if new_book is not already in all_books. """
    
    new_book_title = new_book[0].lower()
    recorded_titles = [book.split(BOOK_SEPARATOR)[0].lower() for book in all_books]
    return new_book_title not in recorded_titles

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

def get_newest_tweet_id (tweets):
    return max([tweet.id for tweet in tweets])

def get_oldest_tweet_id (tweets):
    return min([tweet.id for tweet in tweets])

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
    # Check and update activities
    activity_updates = get_activity_updates(posts, HASHTAGS)
    update_activities(activity_updates)
    if VERBOSE:
        print('Activity updates: {}'.format(activity_updates))

    # Check and update books
    new_books = get_book_updates(posts)
    update_books(new_books)
    if VERBOSE:
        print('Book updates: {}'.format(new_books))
    
    log_check()
    return

def no_update():
    if VERBOSE:
        print("Nothing new...")
    log_check()

def log_check():
    log("Last check: {} {}".format(time.asctime(time.gmtime()), "GMT"))

def log (info, filename=LOG_FILENAME) :
    """ Writes "info" string to filename. Uses append mode for opening file.""" 
    with open(filename, WRITE_ONLY) as log_file :
        log_file.write("{}\n".format(info))


def write_tweets_to_file(tweets, filename):
    """ Write all tweets to filename. """

    # SET ONLY FOR EXTENDED MODE !!!
    with open(filename, APPEND) as tweet_file :
        for (tid, content) in [(post.id, post.full_text.encode(errors='replace')) for post in tweets]:
            tweet_file.write('{} : {}\n'.format(tid, content))
    

def read_tweet_id(filename):
    """ Returns tweet id from filename. """
    try:
        with open(filename, READ_ONLY) as tweet_file:
            first_line = tweet_file.readline().strip()
            if first_line:
                last_tweet_id = int(first_line)
            else:
                last_tweet_id = 0

    except IOError:
        try:
            with open(filename, READ_AND_WRITE_NEW_TRUNC) as tweet_file:
                last_tweet_id = 0
        except:
            print("Really can't open that file!")
            print("Quitting...")
            exit(1)

    return last_tweet_id
    
def write_tweet_id(tweet_id, filename):
    """ Write tweet id given to filename. """
    with open(filename, READ_AND_WRITE_NEW_TRUNC) as f:
        f.write('{}\n'.format(tweet_id))


if __name__ == '__main__':

    # Authenticate
    user, ck, cs, atk, ats = get_keys_and_user()
    api = twitter.Api(  consumer_key=ck, consumer_secret=cs, 
                        access_token_key=atk, access_token_secret=ats, 
                        tweet_mode=TWEET_MODE)

    last_tweet_id = read_tweet_id(LAST_TWEET_ID_FILENAME)

    # Check posts
    raw_new_posts = api.GetUserTimeline(screen_name=user, 
                                    since_id=last_tweet_id,
                                    include_rts=False,
                                    trim_user=True
                                    )

    # Extract text
    new_posts = [extract_full_text(post) for post in raw_new_posts]

    # Process if any 
    if new_posts:
        newest_tweet_id = get_newest_tweet_id(raw_new_posts)
        do_update(new_posts)
    else:
        newest_tweet_id = last_tweet_id
        no_update()

    # Record what was processed
    write_tweets_to_file(raw_new_posts, LATEST_TWEETS_FILENAME)
    write_tweet_id(newest_tweet_id, LAST_TWEET_ID_FILENAME)

    # REPORT ALL
    if VERBOSE:
        print("Retrieved {} posts.".format(len(new_posts)))

    if VERBOSE:
        print("Latest tweet id in file:        {}".format(last_tweet_id))
        print("Latest tweet id just retrieved: {}".format(newest_tweet_id))

    if VERBOSE:
        print("Complete!")
