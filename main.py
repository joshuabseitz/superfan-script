import csv
import time
import tweepy
from collections import Counter

# Read inputs.json file
import json
file = open("input.json","r")
inputs = json.loads(file.read())

# Pulling search criteria from input.json
username = inputs["username"]
number_of_tweets = inputs["number_of_tweets"]

# Pulling Twitter API information from input.json
consumer_key=inputs["api_key"]
consumer_secret=inputs["api_key_secret"]
access_key=inputs["access_token"]
access_secret=inputs["access_secret"]
bearer_token=inputs["bearer_token"]

# API Construction
auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_key,access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)
client = tweepy.Client(bearer_token,wait_on_rate_limit=True)

def main():

  # Get a X amount of Tweets from the specified user
  tweet_IDs = getPaginatedTweets(username, number_of_tweets)

  # get last Tweet for reference in replies request (i.e. get repliese since this last Tweet)
  lastTweetId = tweet_IDs[len(tweet_IDs)-1]
  print("Last Tweet ID: ", lastTweetId)

  # get replies
  repliers = getPaginatedReplies(lastTweetId)

  # Get all retweeters of each Tweet
  retweeters = getPaginatedRts(tweet_IDs)

  # Get all likers of each Tweet
  likers = getPaginatedLikes(tweet_IDs)

  # Find the unique fans from the likers, RTers, and repliers list
  unique_fans = (list(dict.fromkeys(retweeters + likers + repliers)))

  print("----- STORING FAN DATA -----")
  data = []
  
  for fan in unique_fans:

    # Count the RTs for each fan
    rtCount = Counter(retweeters)[fan]

    # Count the likes for each fan
    likeCount =  Counter(likers)[fan]

    # Get the followers for each fan
    followers = getFollowerCount(fan)

    # Calculate replies
    replies = Counter(repliers)[fan]

    # Calculate a score for each fan
    score = ((replies*3)+(rtCount*2)+(likeCount))

    # Add this fan and their data to the "Data" list
    data.append([fan,rtCount,likeCount,replies,score,followers])
    
    print("Data stored for: ", fan)

  # Conver the "Data" list to a spreadsheet
  toCsv(data)
  
def toCsv(data):

  # Open or create a CSV file, with "w" or write permission
  f = open("data.csv", "w")

  # initialize the writer
  writer = csv.writer(f)

  # write the header
  writer.writerow(["Username","Retweets","Favorites","Replies","Score","Followers"])

  # write a new row for each fan and their data
  for fan in data:
    writer.writerow(fan)
  f.close()

  print("----- Data written to 'data.csv' file -----")

def getFollowerCount(fan):

  followers = 0

  # try to get follower count
  try:
    user = api.get_user(screen_name=fan)
    followers = user.followers_count

  # skip if it doesn't work, labels it 0
  except:
    pass

  # return that user's follower count
  return(followers)

def getPaginatedReplies(lastTweetID):

  repliers = []

  print("----- GET REPLIES -----")

  # Get replies
  responsePages = tweepy.Cursor(api.search_tweets, q='to:{}'.format(username),
                          since_id=lastTweetID,count=100).pages(number_of_tweets*10)

  # for every reply, append their username
  for response in responsePages:

    for reply in response:
      
      print("Reply from:  ", reply.user.screen_name, " appended.")
      repliers.append(reply.user.screen_name)
  
  return repliers
  
def getPaginatedTweets(username, number_of_tweets):
  
  tweetIdList = []

  print("----- RETRIEVING TWEET IDs -----")

  # Captures all specified Tweets, paginates through multiple pages as needed
  for tweet in tweepy.Cursor(api.user_timeline,screen_name=username,include_rts='false',count=200).items(number_of_tweets):

    # appends the ID of each Tweet
    tweetIdList.append(tweet.id)
    
    print(tweet.id)

  # return the entire list of Tweet IDs
  return(tweetIdList)

def getPaginatedRts(tweetIdList):
  
  print("----- RETRIEVING PAGINATED RETWEETERS -----")

  retweetersList = []

  # for every Tweet
  for tweet in tweetIdList:

    print("Evaluating: ", tweet, " for retweets.")

    # get the retweeters and paginate as needed
    for response in tweepy.Paginator(client.get_retweeters,
                                     tweet):
      # if the response from Twitter's API is not empty
      if(response.meta['result_count']!=0):

        # append each retweeter to an array
        for retweeter in response.data:
          retweetersList.append(retweeter.username)

  # reutrn the list of retweeters
  return(retweetersList)

def getPaginatedLikes(tweetIdList):

  print("----- RETRIEVING PAGINATED LIKERS -----")
  
  userLikeList = []

  # for every Tweet captured
  for tweet in tweetIdList:
    
    print("Evaluating: ", tweet, " for favorites.")

    # get the likers of the Tweet, paginate as needed
    for response in tweepy.Paginator(client.get_liking_users,tweet):

      # if there are likers
      if(response.meta['result_count']!=0):

        # append them
        for like in response.data:
          userLikeList.append(like.username)

  # return the list of likers
  return(userLikeList)

main()
