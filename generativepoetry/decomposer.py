import random
import re
from collections import defaultdict
from typing import List, TypeVar
import inflect
import markovify
import nltk
import spacy
from gutenberg.acquire import load_etext
from gutenberg.query import get_metadata
from gutenberg.cleanup import strip_headers
from gutenberg_cleaner import super_cleaner
from internetarchive import download
from urllib.parse import urlsplit


sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
spacy_nlp = spacy.load('en_core_web_sm', disable=['ner'])
spacy_nlp.remove_pipe("parser")
inflector = inflect.engine()
input_type = TypeVar('input_type', str, List[str])  # Must be str or list of strings


class ParsedText:

    def __init__(self, text):
        self.raw_text = text
        self.sentences = sent_detector.tokenize(text)
        self.paragraphs = self.raw_text.split("\n\n")

    def random_sentence(self, minimum_tokens=1) -> str:
        """Returns a random sentence from the text.

        Keyword Arguments:
            minimum_tokens; allows for sampling a sentence of a minimum NLP tokens
        """
        num_tokens = 0
        while num_tokens < minimum_tokens:
            sentence = random.choice(self.sentences)
            num_tokens = len([token.text for token in spacy_nlp(sentence)])
        return sentence

    def random_sentences(self, num=5, minimum_tokens=1) -> list:
        """Returns a random sentence from the text.

        Keyword Arguments:
            minimum_tokens; allows for sampling a sentence of a minimum NLP tokens
        """
        random_sentences = []
        while len(random_sentences) < num:
            random_sentence = self.random_sentence(minimum_tokens=minimum_tokens)
            if random_sentence not in random_sentences:
                random_sentences.append(random_sentence)
        return random_sentences

    def random_paragraph(self, minimum_sentences=3) -> str:
        """Returns a random sentence from the text.

        Keyword Arguments:
            minimum_tokens; allows for sampling a sentence of a minimum NLP tokens
        """
        num_sentences = 0
        while num_sentences < minimum_sentences:
            paragraph = random.choice(self.paragraphs)
            num_sentences = len(sent_detector.tokenize(paragraph))
        return paragraph


def validate_url(url, expected_netloc=''):
    """Validate that the provided string is indeed a URL from the anticipated source

     Keyword arguments:
        expected_netloc (str) -- the expected site the URL should be from, i.e. archive.org or gutenberg.org
    """
    url_parts = urlsplit(url)
    if not url_parts.netloc or (expected_netloc and expected_netloc not in url_parts.netloc):
        raise Exception(f'Not a valid f{expected_netloc} document url')


def get_internet_archive_document(url) -> str:
    """Downloads a document (book, etc.) from Internet Archive and returns it as a string. The linked document must
       have a text version. PDF text extraction is not supported at this time.
       Returns a ParsedText instance.
    """
    validate_url(url, expected_netloc='archive.org')
    url_parts = urlsplit(url).path.split("/")
    if len(url_parts) > 2:
        document_id = url_parts[2]
    else:
        raise Exception(f'Not a valid url')
    try:
        response = download(document_id, glob_pattern="*txt", return_responses=True)[0]
        # Remove single newlines, preserve double  newlines (because they demarcate paragraphs
        text = re.sub('(?<![\r\n])(\r?\n|\n?\r)(?![\r\n])', ' ', response.text.strip())
        # This usually creates double spaces between lines because most lines end with single spaces, but to account
        # for cases in which lines end without spaces, we will handle this in two lines
        return re.sub('(?<=[\S])(\s\s)(?=[\S])', ' ', text)

    except Exception:
        raise Exception(f'Archive.org download failed for url: {url}')


def get_gutenberg_document(url) -> str:
    """Downloads a document (book, etc.) from Project Gutenberg and returns it as a string.

    Returns a ParsedText instance."""
    # Get Project Gutenberg document ID from url string
    validate_url(url, expected_netloc='gutenberg.org')
    match = re.search("(?:files|ebooks|epub)\/(\d+)", urlsplit(url).path)
    if not match:
        raise Exception('Not a valid url')
    document_id = int(match.group(1))
    return super_cleaner(strip_headers(load_etext(document_id).strip()), mark_deletions=False)


def random_gutenberg_document(language_filter='en') -> str:
    """Downloads a random document (book, etc.) from Project Gutenberg and returns it as a string.

    Keyword arguments:
        language_filter (str) -- restrict the random document to a paritcular language (default: English)
    """
    doc_language = None
    document = ''
    while (not doc_language or language_filter) and doc_language != language_filter and len(document) == 0:
        # Keep grabbing random documents until 1 meets the language filter, if specified, and verify it really has text
        document_id = random.randint(1, 60134)  # Pick book at random (max id is currently 60134)
        lang_metadata = get_metadata('language', document_id)
        doc_language = next(iter(lang_metadata)) if len(lang_metadata) else False
        document = super_cleaner(strip_headers(load_etext(document_id).strip()), mark_deletions=False)
    return document


def reconcile_replacement_word(original_word_with_ws, original_word_tag, replacement_word, replacement_word_tag) -> str:
    """Modify replacement word if needed to fix subject/verb agreement and preserve the whitespace or lack of before
    and after the original word.

    Arguments:
        original_word_with_ws (str): (str) original word with surrounding whitespace
        original_word_tag (str): part-of-speech tag of original word
        replacement_word (str): word that is replacing original word
        replacement_word_tag (str):  part-of-speech tag of replacement word
    """
    # Pluralize or singularize the replacement word if we're dealing with nouns and one's plural and one's singular.
    if original_word_tag == 'NNS' and replacement_word_tag == 'NN':
        replacement_word = inflector.plural(replacement_word)
    elif original_word_tag == 'NN' and replacement_word_tag == 'NNS':
        replacement_word = inflector.singular_noun(replacement_word) \
            if inflector.singular_noun(replacement_word) else replacement_word
    #  Use regex to preserve the whitespace of the word-to-be-replaced
    replacement_word = re.sub('(?<!\S)\S+(?!\S)', replacement_word, original_word_with_ws)
    return replacement_word


def swap_parts_of_speech(text1, text2, parts_of_speech=['ADJ', 'NOUN']) -> (str, str):
    """Swap all the words of certain parts of speech from one text with those (with the same part of speech) from
    another text.

    Keyword arguments:
        parts_of_speech (list) -- list of parts of speech tags to swap out. Must be from the list provided by spaCy:
                                  https://spacy.io/api/annotation#pos-tagging
    """
    doc1 = spacy_nlp(text1)
    doc2 = spacy_nlp(text2)
    # First build two dictionaries (one for each text) whose keys are parts of speech and values are lists of words
    doc1_words_keyed_by_pos, doc2_words_keyed_by_pos = defaultdict(lambda: []), defaultdict(lambda: [])
    for token in doc1:
        if token.pos_ in parts_of_speech and not token.text in doc1_words_keyed_by_pos[token.pos_]:
            doc1_words_keyed_by_pos[token.pos_].append((token.text, token.tag_))
    for pos in parts_of_speech:
        random.shuffle(doc1_words_keyed_by_pos[pos])  # For variety's sake
    # Also build two dictionaries to store the word swaps we will do at the end. (Token text is immutable in spaCy.)
    # We can simultaneously build the second text's word-by-part-of-speech dict and its word swap dict
    text1_word_swaps, text2_word_swaps = {}, {}
    for token in doc2:
        if token.pos_ in parts_of_speech:
            doc2_words_keyed_by_pos[token.pos_].append((token.text, token.tag_))
            try:
                replacement_word, replacement_word_tag = doc1_words_keyed_by_pos[token.pos_].pop()
                replacement_word = reconcile_replacement_word(token.text_with_ws, token.tag_, replacement_word,
                                                              replacement_word_tag)
                text2_word_swaps[token.text_with_ws] = replacement_word
            except IndexError:  # There are no more words to substitute; the other text had more words of this p.o.s.
                pass
    for pos in parts_of_speech:
        random.shuffle(doc2_words_keyed_by_pos[pos])
    for token in doc1:
        if token.pos_ in parts_of_speech:
            try:
                replacement_word, replacement_word_tag = doc2_words_keyed_by_pos[token.pos_].pop()
                replacement_word = reconcile_replacement_word(token.text_with_ws, token.tag_, replacement_word,
                                                              replacement_word_tag)
                text1_word_swaps[token.text_with_ws] = replacement_word
            except IndexError:  # There are no more words to substitute; the other text had more words of this p.o.s.
                pass
    # Recompose the text from its whitespace-aware tokens, substituting words if needed.
    text1 = ''.join([text1_word_swaps.get(token.text_with_ws, token.text_with_ws) for token in doc1])
    text2 = ''.join([text2_word_swaps.get(token.text_with_ws, token.text_with_ws) for token in doc2])
    return text1, text2

def markov(input: input_type, ngram_size=1, num_output_sentences=5) -> List[str]:
    """Markov chain text generation from markovify library, supports custom n-gram length

    Keyword arguments:
    n-gram size: determines what n-gram model to use: x where x is order-x n-gram
    num_output_sentences: number of sentencess to output
    """
    if type(input) == list:
        list_of_texts = input
    elif type(input) == str:
        list_of_texts = [input]
    markov_models = []
    for text in list_of_texts:
        markov_models.append(markovify.Text(text, state_size=ngram_size))
    textgen = markovify.combine(markov_models)
    output_sentences = []
    while len(output_sentences) < num_output_sentences:
        sentence = textgen.make_sentence()
        if isinstance(sentence, str):
            output_sentences.append(sentence)
    return output_sentences


def cutup(input, min_cutout_words=3, max_cutout_words=7) -> List[str]:
    """Simulates William S. Burroughs' and Brion Gysin's cut-up technique by separating an input text into
    non-whitespace blocks of text and then randomly grouping those into cut-outs between the minimum and maximum
    length of words.

    Arguments:
        input (str) -- input string to be cut up
        min_cutout_words (int) -- minimum number of words in cut out chunk
        max_cutout_words -- maximum number of words in cutout chunk
    """
    if type(input) == list:
        list_of_texts = input
    elif type(input) == str:
        list_of_texts = [input]
    # We don't need tokenization for this since physically cutting up text out of books always cuts where whitespace
    # exists--it does not separate words from punctuation as punctuation does. (Also this way is faster.)
    cutouts = []
    for text in list_of_texts:
        word_list = text.split(" ")
        current_position, next_position = 0, 0
        while next_position < len(word_list):
            cutout_word_count = random.randint(min_cutout_words, max_cutout_words)
            next_position = current_position + cutout_word_count
            cutouts.append(" ".join(word_list[current_position:next_position]))
            current_position = next_position
    random.shuffle(cutouts)
    return cutouts
