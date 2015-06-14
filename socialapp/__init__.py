import twitter
import datetime
#twitter.exec_Twitter_Streamer()

from mediapowerapp.tasks import *
t = twitter.exec_Twitter_Streamer.delay()
