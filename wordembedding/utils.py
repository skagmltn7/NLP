import re
from konlpy.tag import Okt
from basefunction import json2list
from numpy import dot
from numpy.linalg import norm
import kss
from Summarization.textrankr2 import TextRank

def word_embedding(keyword, model):
    wordset=[]
    for similiarity, word in model.get_nearest_neighbors(keyword,20):
        #print(f'{word}:{similiarity}')
        if keyword not in word:
            if kor_chk(word) :
                wordset = wordem_chk(word,wordset)
                if len(wordset)==5:
                    return wordset
    return wordset


def kor_chk(word):
    hangul = re.compile('[^ ㄱ-ㅣ가-힣]+').sub('',word)
    return len(hangul)


def wordem_chk(chkword, wordset):
    if len(wordset) == 0:
        wordset.append(chkword)
        return wordset

    for word in wordset:
        if word not in chkword:
            wordset.append(chkword)
            return wordset
    
    return wordset

def cos_sim(word1, word2):
    if (norm(word1) * norm(word2)) == 0.0:
        return 0
    return dot(word1, word2) / (norm(word1) * norm(word2))


def title_noun(title):
    okt = Okt()
    title_set = okt.nouns(title)

    return title_set
    
def script_noun(json_file):
    script = script_list2str(json_file)
    okt = Okt()
    NounResult = okt.nouns(script)

    return NounResult

def script_list2str(json_file):
    scriptfile = json2list(json_file)
    script_text = ''.join(scriptfile)
    return script_text

def word_set(noun_set):
    word_list=list()
    for word in noun_set:
        if word not in word_list:
            word_list.append(word)
    return word_list

def split_sentence(json_file):
    script = json2list(json_file)
    sentence_text= ''
    for line in script:
        for sent in kss.split_sentences(line):
            sent = sent + '\n'
            sentence_text += sent
    return sentence_text


class okt_tokenizer:
    okt = Okt()
    def __call__(self, text):
        tokens = self.okt.pos(text)
        return tokens