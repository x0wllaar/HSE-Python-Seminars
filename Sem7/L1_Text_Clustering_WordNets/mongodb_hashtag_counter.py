import argparse
from tqdm import tqdm
from pymongo import MongoClient

from dateutil import parser as dateparser

from operator import itemgetter
import pprint



DB_NAME = "TEXTDB"
COLL_NAME = "TEXTCOLL"

parser = argparse.ArgumentParser(description = "Takes  preprocessed texts from MongoDB and counts hashtags")
parser.add_argument("--mongourl", "-d", type=str, default="mongodb://localhost:31415", help="MongoDB URL")
parser.add_argument("--output", "-o", type=str, required=True, help = "Output text file")

parser.add_argument("--datefrom", "-f" , type=str,  default = "1970-01-01", help = "Date from which to look for documents")
parser.add_argument("--dateto", "-t" , type=str,  default = "2999-12-31", help = "Date to which to look for documents")

args = parser.parse_args()

DATE_FROM = dateparser.parse(args.datefrom)
DATE_TO = dateparser.parse(args.dateto)


print("Connecting to DB")
client = MongoClient(args.mongourl)
db = client[DB_NAME]
collection = db[COLL_NAME]

print(f"Finding texts from {DATE_FROM} to {DATE_TO} that are preprocessed")
toCount = collection.find( {'published': {'$lt': DATE_TO, '$gte': DATE_FROM}, 'blueText' : {'$exists': True}}, {"blueText" : 1})

print(f"Found {toCount.count()} texts")

print("Counting #tags")
tagCount = dict()
with tqdm(total=toCount.count()) as pbar:
    for doc in toCount:
        cText = doc['blueText']
        
        cText = cText.replace("\n", " ")

        textWords = cText.split(" ")
        textWords = [w for w in textWords if len(w) > 0]
        
        rawTags = [w for w in textWords if w[0] == "#"]
        procTags = [tag.split("#") for tag in rawTags]
        procTags = [item for sublist in procTags for item in sublist]
        procTags = [t.lower() for t in procTags if len(t) > 0]
        procTags = [f"#{t}" for t in procTags]
        
        for t in procTags:
            if t not in tagCount:
                tagCount[t] = 0

            tagCount[t] += 1

        pbar.update(1)

print(f"Saving outputs to {args.output}")
toptags = sorted(tagCount.items(), key=itemgetter(1), reverse=True)
with open(args.output, "w+") as of:
    print("#tag scores:", file = of)
    pprint.pprint(toptags, stream = of)

print("Top-50 #tags:")
pprint.pprint(toptags[:50])