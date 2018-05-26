import publish

class Post:
    def __init__(self, text):
        self.text = text

book_posts = [
    Post("I just #finished Where the Red Fern Grows by I. Forgot"),
    Post("I just #finished Where and How to Say Goobye by Linus Torvalds"),
    Post("I just #finished the Bible")
]

books = (
    ("Where the Red Fern Grows", "I. Forgot", None),
    ("Where and How to Say Goobye", "Linus Torvalds", None),
    ("the Bible", '', None)
)

activity_posts = [
    Post("Having so much fun #researching biometrics."),
    Post("Just started #tryingout pilates"),
    Post("Mood: Hipster. #listening to Chvrches"),
    Post("I am now #memorizing the dictionary"),
    Post("Took a class. I'm #learning how to knit."),
    Post("Hemingway is good. Currently #reading The Old Man and the Sea."),
    Post("So good. #thankfulfor a place to call home")
]

activities = (
    ("#researching", "biometrics"),
    ("#tryingout", "pilates"),
    ("#listening to", "Chvrches"),
    ("#memorizing", "the dictionary"),
    ("#learning", "how to knit"),
    ("#reading", "The Old Man and the Sea"),
    ("#thankfulfor", "a place to call home")
)

test_posts = []
test_posts.extend(activity_posts)
test_posts.extend(book_posts)

def test_activity_scanner(test_posts):
   
    print("Testing activity scanner...") 

    updates = publish.get_activity_updates(test_posts, publish.HASHTAGS)
    ground_truth = activities

    print ("Results:      {}".format(updates))
    print ("Ground truth: {}".format(ground_truth))

    assert updates == ground_truth 
    return

def test_book_scanner(test_posts):
   
    print("Testing book scanner...") 

    updates = publish.get_book_updates(test_posts) 
    ground_truth = books 

    print ("Results:      {}".format(updates))
    print ("Ground truth: {}".format(ground_truth))
    
    assert updates == ground_truth
    return 

def test_book_converter():
    text = "Finally #finished The Hobbit by J.R.R. Tolkien"

    new_book = publish.extract_book_from_string(text)
    ground_truth = publish.Book("The Hobbit", "J.R.R. Tolkien") 
    
    print ("Results:      {}".format(new_book))
    print ("Ground truth: {}".format(ground_truth))

    assert new_book == ground_truth
    return 

def do_all_tests():

    print("Starting tests...")
    print("Using posts...")
    print test_posts
    #for post in test_posts:
    #    print post.text

    test_book_converter()

    test_activity_scanner(test_posts)
    test_book_scanner(test_posts)

    print("All tests complete!")


if __name__ == "__main__":
    do_all_tests() 
