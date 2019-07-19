import re
import random
import pronouncing
import hunspell
from wordfreq import word_frequency
from datamuse import datamuse

api = datamuse.Datamuse()
hobj = hunspell.HunSpell('/usr/share/hunspell/en_US.dic', '/usr/share/hunspell/en_US.aff')
default_connectors = [' ', '   ', '...   ', random.choice([' & ', ' and ']), '  or  ', ' or ']
line_enders = ['.', ', ', '!', '?', '', ' or', '...']
line_indents = ['', '    ', '         ']
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


def too_similar(word1, word2):
    if not isinstance(word1, str) or not isinstance(word2, str) or len(word1) == 0 or len(word2) == 0:
        return False
    if word1 == word2:
        return True
    if word1 + 's' == word2 or word2 + 's' == word1:
        return True
    return False


def filter_word(string, spellcheck=True):
    validate_str(string)
    if len(string) < 3:
        return False
    if has_invalid_characters(string):
        return False
    if word_frequency(string, 'en') < word_frequency_threshold:
        return False
    if spellcheck and not hobj.spell(string):
        return False
    return True


def filter_word_list(word_list, spellcheck=True):
    word_list = list(
        filter(
            lambda word: filter_word(word, spellcheck=spellcheck), word_list
        )
    )
    return word_list


def rhymes(word, sample_size=None):
    rhymes = filter_word_list([word for word in set(pronouncing.rhymes(word))])
    if isinstance(sample_size, int) and sample_size < len(rhymes):
        rhymes = random.sample(rhymes, k=sample_size)
    random.shuffle(rhymes)
    return rhymes


def rhyme(word):
    """Substitute random rhyme if at least one is found"""
    rhyme_list = rhymes(word)
    if len(rhyme_list):
        return next(iter(rhyme_list), None)
    return None


def extract_sample(word_list, sample_size=None):
    if not sample_size or len(word_list) <= sample_size:
        # Return all results returned by API that pass filter
        return random.sample(word_list, k=len(word_list))
    else:
        sample = []
        while len(sample) < sample_size and len(word_list) > 0:
            sample += [word for word in random.sample(word_list, k=sample_size) if word not in sample]
            word_list = [word for word in word_list if word not in sample]
        if sample_size < len(sample):
            return random.sample(sample, k=sample_size)
        return sample


def similar_sounding_words(input_word, sample_size=6, datamuse_api_max=50):
    validate_word(input_word)
    response = api.words(sl=input_word, max=datamuse_api_max) if datamuse_api_max else api.words(sl=input_word)
    word_list = filter_word_list([obj['word'] for obj in response])
    if input_word in word_list:
        word_list.remove(input_word)
    return extract_sample(word_list, sample_size=sample_size)


def similar_sounding_word(input_word, datamuse_api_max=15):
    return next(iter(similar_sounding_words(input_word, sample_size=1, datamuse_api_max=datamuse_api_max)), None)


def similar_meaning_words(input_word, sample_size=6, datamuse_api_max=20):
    validate_word(input_word)
    response = api.words(ml=input_word, max=datamuse_api_max) if datamuse_api_max else api.words(sl=input_word)
    word_list = filter_word_list([obj['word'] for obj in response], spellcheck=False)
    return extract_sample(word_list, sample_size=sample_size)


def similar_meaning_word(input_word, datamuse_api_max=10):
    return next(iter(similar_meaning_words(input_word, sample_size=1, datamuse_api_max=datamuse_api_max)), None)


def intratextually_associated_words(input_word, sample_size=6, datamuse_api_max=20):
    validate_word(input_word)
    response = api.words(rel_trg=input_word, max=datamuse_api_max) if datamuse_api_max else api.words(sl=input_word)
    word_list = filter_word_list([obj['word'] for obj in response], spellcheck=False)  # Spellcheck removes proper nouns
    return extract_sample(word_list, sample_size=sample_size)


def intratextually_associated_word(input_word, datamuse_api_max=10):
    return next(iter(intratextually_associated_words(input_word, sample_size=1, datamuse_api_max=datamuse_api_max)),
                None)


def phonetically_related_words(input, sample_size=None):
    #  Get all rhymes and similar sounding words to a word or list of words
    if isinstance(input, str):
        input_words = [input]
    elif isinstance(input, list):
        validate_str_list(input, msg='Must provide a string or list of strings')
        input_words = input
    else:
        raise ValueError('Must provide a string or list of strings')

    pr_words = []
    for word in input_words:
        pr_words.extend(rhymes(word, sample_size=sample_size))
        pr_words.extend(w for w in similar_sounding_words(word, sample_size=sample_size)
                        if w not in pr_words)  # eliminate overlap
        if sample_size and sample_size - 1 < len(pr_words):
            pr_words = random.sample(pr_words, k=sample_size)
    return pr_words


def poem_line_from_word_list(word_list, max_line_length=35, connectors=default_connectors):
    output, last_word = word_list[0], word_list[0]
    connector, last_connector = None, None
    for word in word_list[1:]:
        if random.random() < (.2 + len(output)/100):  # Increasing probability of line termination as line gets longer
            break
        if too_similar(last_word, word):
            continue
        connector_choices = [conn for conn in connectors if conn != last_connector]
        output += random.choice(connector_choices) + word
        last_connector = connector
        last_word = word
        if len(output) >= max_line_length:
            break
    return output


def poem_from_word_list(input_word_list, lines=6, link_line_to_input_word=False):
    connectors = [' ', '   ', '...   ', random.choice([' & ', ' and ']), '  or  ', ' or ']
    if random.random() > .7:
        connectors.append(' -> ')
    output, line_indent = '', ''
    if link_line_to_input_word:
        # Only use the phonetically related words for one input word to generate a poem line
        for i in range(lines - 1):
            linked_word = random.choice(input_word_list)
            output += poem_line_from_word_list(phonetically_related_words(linked_word), connectors=connectors)
            line_indent = random.choice(line_indents) if line_indent == '' else \
                random.choice([li for li in line_indents if li is not line_indent])  # Don't repeat the same indent 2x
            output += random.choice(line_enders) + '\n' + line_indent
    else:
        word_list = input_word_list.copy()
        for word in input_word_list:
            word_list.extend(phonetically_related_words(word))
        for i in range(lines - 1):
            random.shuffle(word_list)
            output += poem_line_from_word_list(word_list, connectors=connectors)
            line_indent = random.choice(line_indents) if line_indent == '' else \
                random.choice([li for li in line_indents if li is not line_indent])   # Don't repeat the same indent 2x
            output += random.choice(line_enders) + '\n'+ line_indent

    output += random.choice(input_word_list[:-1]) + ' ' + input_word_list[-1]
    return output


def print_poem(poem):
        print('\n')
        print(poem)
        print('\n')