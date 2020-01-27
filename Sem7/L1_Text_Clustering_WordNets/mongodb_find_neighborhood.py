import argparse
from tqdm import tqdm
from pymongo import MongoClient

from dateutil import parser as dateparser

from operator import itemgetter
import pprint



DB_NAME = "TEXTDB"
COLL_NAME = "TEXTCOLL"

parser = argparse.ArgumentParser(description = "Takes lemmatized texts and creates a disgostic report with important keywords and keyphrases")
parser.add_argument("--mongourl", "-d", type=str, default="mongodb://localhost:31415", help="MongoDB URL")
parser.add_argument("--output", "-o", type=str, required=True, help = "Output text file")
parser.add_argument("--stopwords", "-s", type=str, required=True, help = "Path to a list of stopwords")
parser.add_argument("--minlen", type=int, default=0, help = "A length below or at which all words will be treated as stopwords")
parser.add_argument("--seedword", type=str, default="росатом", help = "Word for which to find neighbors")
parser.add_argument("--window", "-w", type=int, default=3, help="How far from the seed word to look")

parser.add_argument("--datefrom", "-f" , type=str,  default = "1970-01-01", help = "Date from which to look for documents")
parser.add_argument("--dateto", "-t" , type=str,  default = "2999-12-31", help = "Date to which to look for documents")

args = parser.parse_args()

DATE_FROM = dateparser.parse(args.datefrom)
DATE_TO = dateparser.parse(args.dateto)

print("Loading stopwords")
stopwords = set(open(args.stopwords,"r").read().split("\n"))
print(f"{len(stopwords)} stopwords loaded from {args.stopwords}")

print("Connecting to DB")
client = MongoClient(args.mongourl)
db = client[DB_NAME]
collection = db[COLL_NAME]

print(f"Finding texts from {DATE_FROM} to {DATE_TO} that are lemmatized")
toLemmatize = collection.find( {'published': {'$lt': DATE_TO, '$gte': DATE_FROM}, 'processedLemmas' : {'$exists': True}}, {"processedLemmas" : 1})

print(f"Found {toLemmatize.count()} texts")

print("Counting words")
wordCounts = dict()
with tqdm(total=toLemmatize.count()) as pbar:
    for doc in toLemmatize:
        fwords = [w for w in doc['processedLemmas'] if (w not in stopwords) and (len(w) > args.minlen)]
        docNeighbors = []
        for wN, w in zip(range(len(fwords)), fwords):
            if w == args.seedword:
                fWord = wN - args.window
                if fWord < 0:
                    fWord = 0
                lWord = wN + args.window + 1
                docNeighbors += fwords[fWord:lWord]
        for n in docNeighbors:
            if n not in wordCounts:
                wordCounts[n] = 0
            
            wordCounts[n] += 1
        pbar.update(1)

wordCounts.pop(args.seedword, None)

print(f"Saving outputs to {args.output}")
kw_s = sorted(wordCounts.items(), key=itemgetter(1), reverse=True)
with open(args.output, "w+") as of:
    print("Keyword scores:", file = of)
    pprint.pprint(kw_s, stream = of)

print("Top-50 words:")
pprint.pprint(kw_s[:50])