__author__ = 'anil'
from socialapp.apis import twitter

#twitter.exec_Subscriber_Timeline_API()
#twitter.exec_Subscriber_Followers_API()
#twitter.exec_Twitter_Streamer()
#twitter.exec_Twitter_HashTag_Streamer()

subscriber_timeline_task=twitter.exec_Subscriber_Timeline_API.delay()
#subscriber_followers_task=twitter.exec_Subscriber_Followers_API.delay()
#subscriber_twitter_task = twitter.exec_Twitter_Streamer.delay()
#hashtag_twitter_task = twitter.exec_Twitter_HashTag_Streamer.delay()