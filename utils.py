import re
import random
import pronouncing
import hunspell
from wordfreq import word_frequency
from datamuse import datamuse

line_enders = ['.', ', ', '!', '?']
word_frequency_threshold = 4e-08


def validate_str(input, msg='Not a string'):
    if not isinstance(input, str):
        raise ValueError(msg)


def validate_str_list(input, msg='Not a list'):
    if not isinstance(input, list):
        raise ValueError(msg)
    for i, elem in enumerate(input):
        if not isinstance(elem, str):
            raise ValueError(f'Element {i + 1} not a string')


def has_invalid_characters(string):
    return bool(re.search(r"[\s\d\-\']", string))  # Whitespace, digits, hyphens not allowed


def validate_word(string):
    validate_str(string)
    if has_invalid_characters(string):
        raise ValueError('Word may not contain digits, spaces, or special characters.')

def filter_word(string):
    validate_str(string)
    if len(string) < 3:
        return False
    if has_invalid_characters(string):
        return False
    if word_frequency(string, 'en') < word_frequency_threshold:
        return False
    return True


def filter_word_list_quick(word_list):
    word_list = list(
        filter(
            lambda word: filter_word(word), word_list
        )
    )
    return word_list


def filter_word_list_spellcheck(word_list):
    hobj = hunspell.HunSpell('/usr/share/hunspell/en_US.dic', '/usr/share/hunspell/en_US.aff')
    return list(
        filter(lambda word: hobj.spell(word), word_list)
    )


def rhymes(word, sample_size=None):
    rhymes = filter_word_list_spellcheck(filter_word_list_quick([word for word in set(pronouncing.rhymes(word))]))
    if isinstance(sample_size, int) and sample_size < len(rhymes):
        rhymes = random.sample(rhymes, k=sample_size)
    random.shuffle(rhymes)
    return rhymes


def rhyme(word):
    """Substitute random rhyme if at least one is found"""
    rhyme_list = rhymes(word)
    if len(rhyme_list):
        return next(iter(rhyme_list))
    return None

def similar_sounding_words(input_word, sample_size=6, datamuse_api_max=48):
    validate_word(input_word)
    api = datamuse.Datamuse()
    response = api.words(sl=input_word, max=datamuse_api_max)
    word_list = filter_word_list_quick([obj['word'] for obj in response])
    if not sample_size or len(word_list) <= sample_size:
        # Return all results returned by API that pass filter
        similar_sounding_words = filter_word_list_spellcheck(word_list)
        random.shuffle(similar_sounding_words)
        return similar_sounding_words
    else:
        similar_sounding_words = list()
        while len(similar_sounding_words) < sample_size and len(word_list) > 0:
            if sample_size < len(word_list):
                sample = random.sample(word_list, k=sample_size)
            similar_sounding_words.extend(filter_word_list_spellcheck(sample))
            word_list = [word for word in word_list if word not in sample]
        if sample_size < len(similar_sounding_words):
            return random.sample(similar_sounding_words, k=sample_size)
        return similar_sounding_words


def similar_sounding_word(input_word, datamuse_api_max=15):
    return similar_sounding_words(input_word, sample_size=1, datamuse_api_max=datamuse_api_max)[0]


def phonetically_related_words(input, sample_size=None):
    #  Get all rhymes and similar sounding words to a word or list of words

    if isinstance(input, str):
        input_words = [input]
    elif isinstance(input, list):
        validate_str_list(input, msg='Must provide a string or list of strings')
        input_words = input
    else:
        import ipdb; ipdb.set_trace()
        raise ValueError('Must provide a string or list of strings')

    for word in input_words:
        pr_words = rhymes(word, sample_size=4)
        pr_words.extend(w for w in similar_sounding_words(word, sample_size=5) if w not in pr_words)  # eliminate overlap
        if sample_size and sample_size - 1 < len(pr_words):
            pr_words = random.sample(pr_words, k=sample_size - 1)
    return pr_words


def poem_line_from_word_list(word_list, max_line_length=35):
    connectors = [' ', '   ', '\n    ', '\n        ', '...   ', random.choice([' & ', ' and ']), '  or  ', ' or ']
    if random.random() > .5:
        connectors.append(' -> ')
    output = word_list[0]
    connector, last_connector = None, None
    for w in word_list[1:]:
        # Assumption - no repeat connector
        while connector is None or connector == last_connector:
            connector = random.choice(connectors) if last_connector != '\n    ' else '\n         '
        output += random.choice(connectors) + w
        last_connector = connector
        last_word = w
        if len(output) >= max_line_length:
            break
    output += random.choice(line_enders)
    return output


def poem_from_word_list(input_word_list, lines=5, mix_bursts=True): #push out last 3 words in deque
    output = ''
    if mix_bursts:
        word_list = input_word_list.copy()
        for word in input_word_list:
            word_list.extend(phonetically_related_words(word))
        for i in range(lines):
            random.shuffle(word_list)
            output += poem_line_from_word_list(word_list) + '\n'
    else:
        for word in input_word_list:
            output += poem_line_from_word_list(phonetically_related_words(word), original_word=word) + '\n'
    output += random.choice(input_word_list[:-1]) + ' ' + input_word_list[-1]
    return output
