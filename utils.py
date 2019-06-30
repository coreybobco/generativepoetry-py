import re
import random
import pronouncing
import hunspell
from wordfreq import word_frequency
from datamuse import datamuse

connectors = [' ', '... ', ' and ', ' or \n  ']
ws_connectors = [' ', '   ', '\n    ', ' --> ', '...   ', ' & ', '  or  ']
line_enders = ['.', ', ', '!', '?']

def validate_str(input):
    if not isinstance(input, str):
        raise ValueError('Not a string')

def validate_word(string, single=True):
    validate_str(string)
    if bool(re.search(r"[\s\d\-\']", string)): # Whitespace, digits, hyphens not allowed
        raise ValueError('Word may not contain digits, spaces, or special characters.')

def filter_word(string):
    validate_str(string)
    if len(string) < 3:
        return False
    if bool(re.search(r"[\s\d\-\']", string)): # Whitespace, digits, hyphens not allowed
        return False
    return True

def filter_word_list_quick(word_list, exclude_word=None):
    word_list = list(
        filter(
            lambda word: len(word) > 3 and filter_word(word) and \
                         word_frequency(word, 'en') > 5e-8,
            word_list
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
    return rhymes

def rhyme(word):
    """Substitute random rhyme if at least one is found"""
    return next(iter(get_rhymes(word)))

def random_rhymeburst(word):
    """Substitute 2 random rhyme if at least two are found"""
    # TODO: make this work for more than two words
    rhyme_words = get_rhymes(word)
    if len(rhyme_words) >= 2:
        return f'{rhyme_words.pop(random.randint(0, len(rhyme_words)))}, {random.choice(rhyme_words)}'
    else:
        return random_rhyme(word)

def phonetic_burst(word, sample_size=6):
    word_list = rhymes(word, sample_size=4)
    word_list.extend(w for w in similar_sounding_words(word, sample_size=5) if w not in word_list) #why is there overlap
    if sample_size - 1 < len(word_list):
        word_list = random.sample(word_list, k=sample_size - 1)
    return word_list

def poem_from_word_list(input_word_list, lines=5, mix_bursts=True): #push out last 3 words in deque
    output = ''
    if mix_bursts:
        word_list = phonetic_burst(input_word_list[0])
        for word in input_word_list[1:]:
            word_list.extend(phonetic_burst(word))
        for i in range(lines):
            random.shuffle(word_list)
            output += poem_line_from_word_list(word_list, original_word=word) + '\n'
        return output
    for word in input_word_list:
        output += poem_line_from_word_list(phonetic_burst(word), original_word=word) + '\n'
    return output

def poem_line_from_word_list(word_list, original_word=None, max_line_length=34):
    output = word_list[0]
    for w in word_list[1:]:
        connector, last_connector = None, None
        # Assumption - no repeat connector
        while connector is None or connector == last_connector:
            connector = random.choice(ws_connectors) if last_connector != '\n  ' else  '\n         '
        output += random.choice(ws_connectors) + w
        last_connector = connector
        if len(output) >= max_line_length:
            break
    output += ' ' + original_word if original_word else ' ' + {word_list[-1]}
    output += random.choice(line_enders)
    return output

def similar_sounding_words(input_word, sample_size=6, datamuse_api_max=48):
    validate_word(input_word)
    api = datamuse.Datamuse()
    response = api.words(sl=input_word, max=datamuse_api_max) #+ 1)[1:]  # Remove original word returned by Datamuse API - test for this
    word_list = filter_word_list_quick([obj['word'] for obj in response])
    if len(word_list) <= sample_size:
        return filter_word_list_spellcheck(word_list)
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
