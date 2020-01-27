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

print("Generating candidate phrases")
phrases = []
with tqdm(total=toLemmatize.count()) as pbar:
    for doc in toLemmatize:
        mla = []
        for l in doc['processedLemmas']:
            if (l in stopwords) or (len(l) <= args.minlen):
                mla.append("|")
            else:
                mla.append(l)

        phrasea = [phrase.strip().split(" ") for phrase in (" ".join(mla)).split("|") if phrase.strip() != ""]
        phrases.append(phrasea)
        pbar.update(1)
print("Condidate phrases generated")

print("Computing word scores")
word_frequency = dict()
word_degree = dict()

word_score = dict()

for text in tqdm(phrases):
    for phrase in text:
        phrase_len = len(phrase)
        phrase_degree = phrase_len - 1
        for word in phrase:
            if word not in word_frequency:
                word_frequency[word] = 0
            word_frequency[word] += 1

            if word not in word_degree:
                word_degree[word] = 0
            word_degree[word] += phrase_degree

for word in word_frequency:
    word_degree[word] += word_frequency[word]

for word in word_frequency:
    word_score[word] = word_degree[word] / word_frequency[word]

print(f"Scores computed for {len(word_score)} words")

print(f"Computing scores for phrases")
keyword_candidates = {}
for text in tqdm(phrases):
    for phrase in text:
        sPhrase = " ".join(phrase)

        #if len(sPhrase) > 50:
        #    continue

        cScore = 0
        for word in phrase:
            cScore += word_score[word]
        keyword_candidates[sPhrase] = cScore
print("Scores computed")

print(f"Saving outputs to {args.output}")
kp_s = sorted(keyword_candidates.items(), key=itemgetter(1), reverse=True)
kw_s = sorted(word_score.items(), key=itemgetter(1), reverse=True)
with open(args.output, "w+") as of:
    print("Keyphrases ranked by score:", file = of)
    pprint.pprint(kp_s, stream = of)
    print("\n\n###################\n\nKeyword scores:", file = of)
    pprint.pprint(kw_s, stream = of)

print("Top-10 phrases:")
pprint.pprint(kp_s[:10])
print("")
print("Top-10 words:")
pprint.pprint(kw_s[:10])
