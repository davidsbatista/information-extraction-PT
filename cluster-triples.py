#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import pickle
import numpy as np

import requests
import scipy

from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from extract_ReVerb_patterns_PT import Triple
from sklearn.metrics.pairwise import cosine_distances
from sklearn.metrics.pairwise import pairwise_distances

__author__ = "David S. Batista"
__email__ = "dsbatista@gmail.com"


def generate_embeddings(text):

    embeddings_vector = np.zeros(400)

    for token in text.split():
        try:
            embeddings_vector += get_word_embedding(token)
        except KeyError:
            print "Not Found:", token

        except ValueError:
            print "Value Error:", token

    return embeddings_vector


def get_word_embedding(word):
    payload = {'word': word}
    answer = requests.get('http://127.0.0.1:8889/get_vector?', params=payload)
    return np.array(answer.json()['vector'])


def compute_embeddings_vectors():
    triples = []
    count = 0
    with open('triples.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        for t in reader:
            e1, e1_type, rel, e2, e2_type = t[0], t[1], t[2], t[3], t[4]
            vector = generate_embeddings(rel)
            t = Triple(e1, e1_type, rel, e2, e2_type)
            t.vector = vector
            triples.append(t)
            count += 1
            if count % 10000 == 0:
                print count
    with open('triples_vectors.pkl', 'w') as out_file:
        pickle.dump(triples, out_file)


def compute_pairwise_distances(triples, vectors):
    # size = len(vectors)
    size = 69213
    distances_matrix = np.zeros((size, size))
    for i, ele_1 in enumerate(vectors):
        for j, ele_2 in enumerate(vectors):
            # Matrix is symmetrical, no need to calculate every position
            if j >= i:
                break
            # distance = cosine_distances(ele_1.reshape(1, -1), ele_2.reshape(1, -1))
            distance = cosine_distances(ele_1, ele_2)
            distances_matrix[i, j] = distance[0][0]
            distances_matrix[j, i] = distance[0][0]

        if i % 500 == 0:
            print i

    return distances_matrix


def main():

    """
    compute_embeddings_vectors()
    print "Reading embedding vectors"
    with open('triples_vectors.pkl', 'r') as in_file:
        triples = pickle.load(in_file)
    vectors = []
    for t in triples:
        vectors.append(t.vector)
    """

    text = []
    triples = []
    with open('triples.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        for t in reader:
            e1, e1_type, rel, e2, e2_type = t[0], t[1], t[2], t[3], t[4]
            t = Triple(e1, e1_type, rel, e2, e2_type)
            text.append(rel)
            triples.append(t)

    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(text)

    print "Clustering"
    dbscan = DBSCAN(eps=0.4, min_samples=15, metric='cosine', algorithm='brute',
                    leaf_size=30, p=None, n_jobs=1)
    labels = dbscan.fit_predict(tfidf_matrix)
    with open('triples_labels.txt', 'w') as out_file:
        for l in labels:
            out_file.write(str(l) + '\n')

    print "Reading cluster labels"
    labels = []
    with open('triples_labels.txt', 'r') as in_file:
        for label in in_file:
            labels.append(int(label.strip()))

    for i in range(len(triples)):
        triples[i].label = labels[i]

    clusters = dict()
    for t in triples:
        try:
            clusters[t.label] += 1
        except KeyError:
            clusters[t.label] = 1

    print clusters
    exit(-1)
    # print len(clusters)

    # top-terms for each cluster
    for x in range(-1, len(clusters)):
        print x, len(clusters[x])
        for t in triples:
            if t.label == str(x):
                print t.rel
        print
        print


if __name__ == "__main__":
    main()
