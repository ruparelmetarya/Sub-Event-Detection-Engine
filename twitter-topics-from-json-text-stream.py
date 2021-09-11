# -*- coding: utf-8 -*-

# What this code does:
# Given a Twitter stream in JSON-to-text format, the time window size in minutes (e.g., 15 minutes)
# and the output file name, extract top 10 topics detected in the time window

# Example run:
# python twitter-topics-from-json-text-stream.py json-to-text-stream-syria.json.txt 15 15mins-topics-syria-stream.txt > details_clusters_15mins_topics_syria-stream.txt

import codecs
from collections import Counter
import CMUTweetTagger
from datetime import datetime
import fastcluster
from itertools import cycle
import json
import nltk
import numpy as np
import re
import os
import scipy.cluster.hierarchy as sch
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import preprocessing
from sklearn.metrics.pairwise import pairwise_distances
from sklearn import metrics
import string
import sys
import time

def load_stopwords():
	stop_words = nltk.corpus.stopwords.words('english')
	stop_words.extend(['this','that','the','might','have','been','from',
                'but','they','will','has','having','had','how','went'
                'were','why','and','still','his','her','was','its','per','cent',
                'a','able','about','across','after','all','almost','also','am','among',
                'an','and','any','are','as','at','be','because','been','but','by','can',
                'cannot','could','dear','did','do','does','either','else','ever','every',
                'for','from','get','got','had','has','have','he','her','hers','him','his',
                'how','however','i','if','in','into','is','it','its','just','least','let',
                'like','likely','may','me','might','most','must','my','neither','nor',
                'not','of','off','often','on','only','or','other','our','own','rather','said',
                'say','says','she','should','since','so','some','than','that','the','their',
                'them','then','there','these','they','this','tis','to','too','twas','us',
                'wants','was','we','were','what','when','where','which','while','who',
                'whom','why','will','with','would','yet','you','your','ve','re','rt', 'retweet', '#fuckem', '#fuck',
                'fuck', 'ya', 'yall', 'yay', 'youre', 'youve', 'ass','factbox', 'com', '&lt', 'th',
                'retweeting', 'dick', 'fuckin', 'shit', 'via', 'fucking', 'shocker', 'wtf', 'hey', 'ooh', 'rt&amp', '&amp',
                '#retweet', 'retweet', 'goooooooooo', 'hellooo', 'gooo', 'fucks', 'fucka', 'bitch', 'wey', 'sooo', 'helloooooo', 'lol', 'smfh'])
	stop_words = set(stop_words)
	return stop_words



def normalize_text(text):
	try:
		text = text.encode('utf-8')
	except: pass
	text = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(pic\.twitter\.com/[^\s]+))','', text)
	text = re.sub('@[^\s]+','', text)
	text = re.sub('#([^\s]+)', '', text)
	text = re.sub('[:;>?<=*+()/,\-#!$%\{˜|\}\[^_\\@\]1234567890’‘]',' ', text)
	text = re.sub('[\d]','', text)
	text = text.replace(".", '')
	text = text.replace("'", ' ')
	text = text.replace("\"", ' ')
	text = text.replace("\x9d",' ').replace("\x8c",' ')
	text = text.replace("\xa0",' ')
	text = text.replace("\x9d\x92", ' ').replace("\x9a\xaa\xf0\x9f\x94\xb5", ' ').replace("\xf0\x9f\x91\x8d\x87\xba\xf0\x9f\x87\xb8", ' ').replace("\x9f",' ').replace("\x91\x8d",' ')
	text = text.replace("\xf0\x9f\x87\xba\xf0\x9f\x87\xb8",' ').replace("\xf0",' ').replace('\xf0x9f','').replace("\x9f\x91\x8d",' ').replace("\x87\xba\x87\xb8",' ')
	text = text.replace("\xe2\x80\x94",' ').replace("\x9d\xa4",' ').replace("\x96\x91",' ').replace("\xe1\x91\xac\xc9\x8c\xce\x90\xc8\xbb\xef\xbb\x89\xd4\xbc\xef\xbb\x89\xc5\xa0\xc5\xa0\xc2\xb8",' ')
	text = text.replace("\xe2\x80\x99s", " ").replace("\xe2\x80\x98", ' ').replace("\xe2\x80\x99", ' ').replace("\xe2\x80\x9c", " ").replace("\xe2\x80\x9d", " ")
	text = text.replace("\xe2\x82\xac", " ").replace("\xc2\xa3", " ").replace("\xc2\xa0", " ").replace("\xc2\xab", " ").replace("\xf0\x9f\x94\xb4", " ").replace("\xf0\x9f\x87\xba\xf0\x9f\x87\xb8\xf0\x9f", "")
	return text

def nltk_tokenize(text):
	tokens = []
	pos_tokens = []
	entities = []
	features = []
	try:

			tokens = text.split()

			for word in tokens:
				if word.lower() not in stop_words and len(word) > 1:
						#features.append(word + "." + postag)
					features.append(word)
	except: pass
	return [tokens, pos_tokens, entities, features]

# '''Assumes its ok to remove user mentions and hashtags from tweet text (normalize_text), '''
# '''since we extracted them already from the json object'''
def process_json_tweet(text, fout, debug):
	features = []

	if len(text.strip()) == 0:
		return []
	text = normalize_text(text)
	#print text
	#nltk pre-processing: tokenize and pos-tag, try to extract entities
	try:
		[tokens, pos_tokens, entities, features] = nltk_tokenize(text)
	except:
		print "nltk tokenize+pos pb!"
	if debug:
		try:
			fout.write("\n--------------------clean text--------------------\n")
			fout.write(text.decode('utf-8'))
			#fout.write(text)
			fout.write("\n--------------------tokens--------------------\n")
			fout.write(str(tokens))
	#		fout.write("\n--------------------cleaned tokens--------------------\n")
	#		fout.write(str(clean_tokens))
			fout.write("\n--------------------pos tokens--------------------\n")
			fout.write(str(pos_tokens))
			fout.write("\n--------------------entities--------------------\n")
			for ent in entities:
				fout.write("\n" + str(ent).decode('utf-8'))
			fout.write("\n--------------------features--------------------\n")
			fout.write(str(features))
			fout.write("\n\n")
		except:
			#print "couldn't print text"
			pass
	return features

'''Prepare features, where doc has terms separated by comma'''
def custom_tokenize_text(text):
	REGEX = re.compile(r",\s*")
	tokens = []
	for tok in REGEX.split(text):
		#if "@" not in tok and "#" not in tok:
		if "@" not in tok:
			#tokens.append(stem(tok.strip().lower()))
			tokens.append(tok.strip().lower())
	return tokens

def spam_tweet(text):
	if 'Jordan Bahrain Morocco Syria Qatar Oman Iraq Egypt United States' in text:
		return True

	if 'Some of you on my facebook are asking if it\'s me' in text:
		return True

	if '@kylieminogue please Kylie Follow Me, please' in text:
		return True

	if 'follow me please' in text:
		return True

	if 'please follow me' in text:
		return True

	return False

'''start main'''
if __name__ == "__main__":
	file_timeordered_tweets = codecs.open(sys.argv[1], 'r', 'utf-8')
	time_window_mins = float(sys.argv[2])
	#file_timeordered_news = codecs.open(sys.argv[3], 'r', 'utf-8')
	fout = codecs.open(sys.argv[3], 'w', 'utf-8')

	debug=0
	stop_words = load_stopwords()

	tweet_unixtime_old = -1
	#fout.write("time window size in mins: " + str(time_window_mins))
	tid_to_raw_tweet = {}
	window_corpus = []
	tid_to_urls_window_corpus = {}
	tids_window_corpus = []
	dfVocTimeWindows = {}
	t = 0
	ntweets = 0

#	fout.write("\n--------------------start time window tweets--------------------\n")
	#efficient line-by-line read of big files
	for line in file_timeordered_tweets:
		[tweet_unixtime, tweet_gmttime, tweet_id, text, hashtags, users, urls, nfollowers, nfriends] = eval(line)
		if spam_tweet(text):
			continue
		#fout.write("\n"+ str([tweet_unixtime, tweet_gmttime, tweet_id, text, hashtags, users, urls, media_urls, nfollowers, nfriends]) + "\n")

		if tweet_unixtime_old == -1:
			tweet_unixtime_old = tweet_unixtime

#  		#while this condition holds we are within the given size time window
		if (tweet_unixtime - tweet_unixtime_old) < time_window_mins * 60:
			ntweets += 1

			features = process_json_tweet(text, fout, debug)
			tweet_bag = ""
			try:
				for user in set(users):
					tweet_bag += "@" + user.decode('utf-8').lower() + ","
				for tag in set(hashtags):
					if tag.decode('utf-8').lower() not in stop_words:
						tweet_bag += "#" + tag.decode('utf-8').lower() + ","
				for feature in features:
					tweet_bag += feature.decode('utf-8') + ","
			except:
				#print "tweet_bag error!", tweet_bag, len(tweet_bag.split(","))
				pass

			#print tweet_bag.decode('utf-8')
			if len(users) < 3 and len(hashtags) < 3 and len(features) > 3 and len(tweet_bag.split(",")) > 4 and not str(features).upper() == str(features):
				tweet_bag = tweet_bag[:-1]
				#fout.write(tweet_bag + "\n\n")
				window_corpus.append(tweet_bag)
				tids_window_corpus.append(tweet_id)
				tid_to_urls_window_corpus[tweet_id] = urls
				tid_to_raw_tweet[tweet_id] = text
				#print urls_window_corpus
		else:
				dtime = datetime.fromtimestamp(tweet_unixtime_old).strftime("%d-%m-%Y %H:%M")
				print "\nWindow Starts GMT Time:", dtime, "\n"
				tweet_unixtime_old = tweet_unixtime
				t += 1
				vectorizer = CountVectorizer(tokenizer=custom_tokenize_text, binary=True, min_df=max(int(len(window_corpus)*0.0025), 10), ngram_range=(2,3))

 				X = vectorizer.fit_transform(window_corpus)
 				map_index_after_cleaning = {}
 				Xclean = np.zeros((1, X.shape[1]))
 				for i in range(0, X.shape[0]):
 					#keep sample with size at least 5
 					if X[i].sum() > 4:
 						Xclean = np.vstack([Xclean, X[i].toarray()])
 						map_index_after_cleaning[Xclean.shape[0] - 2] = i
#   					else:
#   						print "OOV tweet:"
#  	 				print map_index_after_cleaning

 				Xclean = Xclean[1:,]
				#print "len(articles_corpus):", len(articles_corpus)
				print "total tweets in window:", ntweets
				#print "len(window_corpus):", len(window_corpus)
				print "X.shape:", X.shape
 				print "Xclean.shape:", Xclean.shape
 				#print map_index_after_cleaning
				#play with scaling of X
				X = Xclean
				Xdense = np.matrix(X).astype('float')
				X_scaled = preprocessing.scale(Xdense)
				X_normalized = preprocessing.normalize(X_scaled, norm='l2')
				#transpose X to get features on the rows
				#Xt = X_scaled.T
# 				#print "Xt.shape:", Xt.shape
 				vocX = vectorizer.get_feature_names()
 				#print "Vocabulary (tweets):", vocX
 				#sys.exit()

 				boost_entity = {}
 				pos_tokens = CMUTweetTagger.runtagger_parse([term.upper() for term in vocX])
 				#print "detect entities", pos_tokens
 				for l in pos_tokens:
 					term =''
 					for gr in range(0, len(l)):
 						term += l[gr][0].lower() + " "
  					if "^" in str(l):
 						boost_entity[term.strip()] = 2.5
 					else:
 				 		boost_entity[term.strip()] = 1.0

				dfX = X.sum(axis=0)
 				#print "dfX:", dfX
 				dfVoc = {}
 				wdfVoc = {}
 				boosted_wdfVoc = {}
 				keys = vocX
 				vals = dfX
 				for k,v in zip(keys, vals):
 					dfVoc[k] = v
 				for k in dfVoc:
 					try:
 						dfVocTimeWindows[k] += dfVoc[k]
 						avgdfVoc = (dfVocTimeWindows[k] - dfVoc[k])/(t - 1)
 						#avgdfVoc = (dfVocTimeWindows[k] - dfVoc[k])
					except:
 						dfVocTimeWindows[k] = dfVoc[k]
 						avgdfVoc = 0

 					wdfVoc[k] = (dfVoc[k] + 1) / (np.log(avgdfVoc + 1) + 1)
					try:
						boosted_wdfVoc[k] = wdfVoc[k] * boost_entity[k]
					except:
						boosted_wdfVoc[k] = wdfVoc[k]
				print "sorted wdfVoc*boost_entity:"
				print sorted( ((v,k) for k,v in boosted_wdfVoc.iteritems()), reverse=True)
				distMatrix = pairwise_distances(X_normalized, metric='cosine')
 				print "fastcluster, average, cosine"
 				L = fastcluster.linkage(distMatrix, method='average')

				dt = 0.5
				print "hclust cut threshold:", dt
#				indL = sch.fcluster(L, dt, 'distance')
				indL = sch.fcluster(L, dt*distMatrix.max(), 'distance')
				#print "indL:", indL
				freqTwCl = Counter(indL)
				print "n_clusters:", len(freqTwCl)
				print(freqTwCl)

				npindL = np.array(indL)
#				print "top50 most populated clusters, down to size", max(10, int(X.shape[0]*0.0025))
				freq_th = max(10, int(X.shape[0]*0.0025))
				cluster_score = {}
	 			for clfreq in freqTwCl.most_common(50):
	 				cl = clfreq[0]
 					freq = clfreq[1]
 					cluster_score[cl] = 0
 					if freq >= freq_th:
 	 					#print "\n(cluster, freq):", clfreq
	 					clidx = (npindL == cl).nonzero()[0].tolist()
						cluster_centroid = X[clidx].sum(axis=0)
						#print "centroid_array:", cluster_centroid
						try:
							#orig_tweet = window_corpus[map_index_after_cleaning[i]].decode("utf-8")
							cluster_tweet = vectorizer.inverse_transform(cluster_centroid)
							#print orig_tweet, cluster_tweet, urls_window_corpus[map_index_after_cleaning[i]]
							#print orig_tweet
							#print "centroid_tweet:", cluster_tweet
							for term in np.nditer(cluster_tweet):
								#print "term:", term#, wdfVoc[term]
								try:
									cluster_score[cl] = max(cluster_score[cl], boosted_wdfVoc[str(term).strip()])
								except: pass
						except: pass
						cluster_score[cl] /= freq
					else: break

				sorted_clusters = sorted( ((v,k) for k,v in cluster_score.iteritems()), reverse=True)
				print "sorted cluster_score:"
		 		print sorted_clusters

		 		ntopics = 20
		 		headline_corpus = []
		 		orig_headline_corpus = []
		 		headline_to_cluster = {}
		 		headline_to_tid = {}
		 		cluster_to_tids = {}
		 		for score,cl in sorted_clusters[:ntopics]:
		 			#print "\n(cluster, freq):", cl, freqTwCl[cl]
		 			clidx = (npindL == cl).nonzero()[0].tolist()
					first_idx = map_index_after_cleaning[clidx[0]]
					keywords = window_corpus[first_idx]
					orig_headline_corpus.append(keywords)
					headline = ''
					for k in keywords.split(","):
						if not '@' in k and not '#' in k:
							headline += k + ","
					headline_corpus.append(headline[:-1])
					headline_to_cluster[headline[:-1]] = cl
					headline_to_tid[headline[:-1]] = tids_window_corpus[first_idx]
 					tids = []
 					for i in clidx:
						idx = map_index_after_cleaning[i]
 						tids.append(tids_window_corpus[idx])
 					cluster_to_tids[cl] = tids
				headline_vectorizer = CountVectorizer(tokenizer=custom_tokenize_text, binary=True, min_df=1, ngram_range=(1,1))
				#headline_vectorizer = TfidfVectorizer(tokenizer=custom_tokenize_text, min_df=1, ngram_range=(1,1))
			  	H = headline_vectorizer.fit_transform(headline_corpus)
			  	print "H.shape:", H.shape
				vocH = headline_vectorizer.get_feature_names()
			  	#print "Voc(headline_corpus):", vocH

			  	Hdense = np.matrix(H.todense()).astype('float')
			  	#Ht = Hdense.T
			  	#print "Ht.shape:", Ht.shape
				#Hdense = Ht
# 			  	distH = pairwise_distances(Hdense, metric='manhattan')
				distH = pairwise_distances(Hdense, metric='cosine')
			  	#distHt = pairwise_distances(Ht, metric='manhattan')
			  	#print distH
#				print "fastcluster, avg, euclid"
 				HL = fastcluster.linkage(distH, method='average')
				dtH = 1.0
				indHL = sch.fcluster(HL, dtH*distH.max(), 'distance')
#				indHL = sch.fcluster(HL, dtH, 'distance')
				freqHCl = Counter(indHL)
				print "hclust cut threshold:", dtH
				print "n_clusters:", len(freqHCl)
				print(freqHCl)

				npindHL = np.array(indHL)
				hcluster_score = {}
	 			for hclfreq in freqHCl.most_common(ntopics):
	 				hcl = hclfreq[0]
 					hfreq = hclfreq[1]
 					hcluster_score[hcl] = 0
					hclidx = (npindHL == hcl).nonzero()[0].tolist()
					for i in hclidx:
						hcluster_score[hcl] = max(hcluster_score[hcl], cluster_score[headline_to_cluster[headline_corpus[i]]])
#					hcluster_score[hcl] /= freq
				sorted_hclusters = sorted( ((v,k) for k,v in hcluster_score.iteritems()), reverse=True)
				print "sorted hcluster_score:"
		 		print sorted_hclusters

				for hscore, hcl in sorted_hclusters[:10]:
#					print "\n(cluster, freq):", hcl, freqHCl[hcl]
	 				hclidx = (npindHL == hcl).nonzero()[0].tolist()
	 				clean_headline = ''
	 				raw_headline = ''
	 				keywords = ''
	 				tids_set = set()
	 				tids_list = []
	 				urls_list = []
	 				selected_raw_tweets_set = set()
	 				tids_cluster = []
 					for i in hclidx:
 						clean_headline += headline_corpus[i].replace(",", " ") + "//"
						keywords += orig_headline_corpus[i].lower() + ","
						tid = headline_to_tid[headline_corpus[i]]
						tids_set.add(tid)
						raw_tweet = tid_to_raw_tweet[tid].encode('utf8', 'replace').replace("\n", ' ').replace("\t", ' ')
						raw_tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(pic\.twitter\.com/[^\s]+))','', raw_tweet)
  						selected_raw_tweets_set.add(raw_tweet.decode('utf8', 'ignore').strip())
  						#fout.write("\nheadline tweet: " + raw_tweet.decode('utf8', 'ignore'))
  						tids_list.append(tid)
  						if tid_to_urls_window_corpus[tid]:
	 						urls_list.append(tid_to_urls_window_corpus[tid])
 						for id in cluster_to_tids[headline_to_cluster[headline_corpus[i]]]:
 							tids_cluster.append(id)

 					raw_headline = tid_to_raw_tweet[headline_to_tid[headline_corpus[hclidx[0]]]]
 					raw_headline = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(pic\.twitter\.com/[^\s]+))','', raw_headline)
 					raw_headline = raw_headline.encode('utf8', 'replace').replace("\n", ' ').replace("\t", ' ')
 					keywords_list = str(sorted(list(set(keywords[:-1].split(",")))))[1:-1].encode('utf8', 'replace').replace('u\'','').replace('\'','')

					#Select tweets with media urls
					#If need code to be more efficient, reduce the urls_list to size 1.
					for tid in tids_cluster:
						if len(urls_list) < 1 and tid_to_urls_window_corpus[tid] and tid not in tids_set:
								raw_tweet = tid_to_raw_tweet[tid].encode('utf8', 'replace').replace("\n", ' ').replace("\t", ' ')
								raw_tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(pic\.twitter\.com/[^\s]+))','', raw_tweet)
 								raw_tweet = raw_tweet.decode('utf8', 'ignore')
 								#fout.write("\ncluster tweet: " + raw_tweet)
 								if raw_tweet.strip() not in selected_raw_tweets_set:
									tids_list.append(tid)
									urls_list.append(tid_to_urls_window_corpus[tid])
									selected_raw_tweets_set.add(raw_tweet.strip())

					try:
						print "\n", clean_headline.decode('utf8', 'ignore')#, "\t", keywords_list
					except: pass

					urls_set = set()
					for url_list in urls_list:
						for url in url_list:
							urls_set.add(url)
							#break
# 					fout.write("\n" + str(list(urls_set))[1:-1][2:-1])

					fout.write("\n" + str(dtime) + "\t" + raw_headline.decode('utf8', 'ignore') + "\t" + keywords_list.decode('utf8', 'ignore') + "\t" + str(tids_list)[1:-1] + "\t" + str(list(urls_set))[1:-1][2:-1].replace('\'','').replace('uhttp','http'))

				#sys.exit()
				window_corpus = []
				tids_window_corpus = []
				tid_to_urls_window_corpus = {}
				tid_to_raw_tweet = {}
				ntweets = 0
				if t == 4:
					dfVocTimeWindows = {}
					t = 0

				

	file_timeordered_tweets.close()
	fout.close()
