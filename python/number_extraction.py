import nltk

with open('sample.txt', 'r') as f:
    sample = f.read()
sample = " is there a zero"
num_dict = ('first','second','third','fourth','for','four','1','2','3','4','one','two','three')
sentences = nltk.word_tokenize(sample)
tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
chunked_sentences = nltk.ne_chunk_sents(tagged_sentences, binary=True)

words = nltk.word_tokenize(sample)
tagged_words = [nltk.pos_tag(word) for word in words]


def extract_number(tagged_words):
    for tag in tagged_words:
        tagged_word = tag[0]
        if tagged_word[1] == 'CD' or tagged_word[1] == 'RB':
            print(tagged_word)
            if tagged_word[0] in num_dict:
                print("****************")
                print(tagged_word[0])

extract_number(tagged_sentences)


