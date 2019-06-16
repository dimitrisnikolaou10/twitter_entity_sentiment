# import libraries 
import pandas as pd
import json
from twython import Twython
import os
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import six
import sys
import time

# Load credentials from json file
with open("twitter_credentials.json", "r") as file:  
    creds = json.load(file)

# Instantiate a twitter object
twitter = Twython(creds['CONSUMER_KEY'], creds['CONSUMER_SECRET'], creds["ACCESS_TOKEN"], creds["ACCESS_SECRET"])
# twitter.verify_credentials()

# Instantiate an NLP object
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="euroleaguenlp.json"
client = language.LanguageServiceClient()

# creating a grid of parameters
parameters = {"geo":
              {"Athens":{"lat":37.9838,"long":23.7275, "radius":50},
               "Thessaloniki":{"lat":40.6401,"long":22.9444, "radius":50},
               "Europe": {"lat":52.5200,"long":13.4050, "radius":1000}},
             "keywords":
              ["syriza","tsipras","nea dimokratia","nd","mitsotakis"]}



text_to_exclude = ["Tsipras_int2"]
users_to_exclude = ["Tsipras_int2"]
inverse_geo_mapping = {}
for area,loc in parameters["geo"].items():
    geo_query=",".join(str(val) for key,val in loc.items())
    geo_query += "mi"
    inverse_geo_mapping[geo_query]=area
	
# Construct list of queries
locations = parameters["geo"]
keywords = parameters["keywords"]

queries = []
for keyword in keywords:
    for area,loc in locations.items():
        geo_query=",".join(str(val) for key,val in loc.items())
        geo_query += "mi"
        query = {
            'q': keyword,  
            'count': 1000,
            'lang': 'en',
            'geocode': geo_query
        }
        queries.append(query)

# Obtain sentiment from each status
def entity_sentiment(text):    
    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    document = types.Document(
        content=text.encode('utf-8'),
        type=enums.Document.Type.PLAIN_TEXT)

    # Detect and send native Python encoding to receive correct word offsets.
    encoding = enums.EncodingType.UTF32
    if sys.maxunicode == 65535:
        encoding = enums.EncodingType.UTF16

    result = client.analyze_entity_sentiment(document, encoding)
    
    return result
	
# Obtain the tweets
start = time.time()
tweets = []
names_of_interest = ["Alexis","Tsipras","Kyriakos","Kiriakos","Mitsotakis"]
for query in queries:
    for status in twitter.search(**query)['statuses']:
        new_tweet = {'user': [], 'date': [], 'text': [], 'favorite_count': []} 
        new_tweet['user'] = status['user']['screen_name']
        new_tweet['date'] = status['created_at']
        new_tweet['text'] = status['text']
        new_tweet['favorite_count'] = status['favorite_count']
        new_tweet['keyword'] = query['q']
        new_tweet['location'] = inverse_geo_mapping[query["geocode"]]
        tweets.append(new_tweet)
        
df = pd.DataFrame(tweets)
df.drop_duplicates(subset="text",inplace=True)
df.reset_index(drop=True, inplace=True)

df["object_of_sentiment"], df["salience"], df["magnitude"], df["sentiment_score"] = None, None, None, None
for i,r in df.iterrows():
    sentiment_result = entity_sentiment(r["text"])
    for entity in sentiment_result.entities:
        if entity.name in names_of_interest:
            df.loc[i,"object_of_sentiment"] = entity.name
            df.loc[i,"salience"] = entity.salience
            df.loc[i,"magnitude"] = entity.sentiment.magnitude
            df.loc[i,"sentiment_score"] = entity.sentiment.score
                
end = time.time()
print("Obtaining the tweets and sentiment took {} seconds.".format(end-start))