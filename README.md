# procedural poetry utils

Run Python interactive shell from Docker

```
docker-compose up -d
docker-compose run app python
```

Things to try:
```
from utils import *
# When sample_size is not provided, all results are returned.
rhymes('cool', sample_size=6) # 6 random rhymes with cool, defaults to all rhymes
['ghoul', 'misrule', 'drool', 'rule', 'uncool', 'spool']

similar_sounding_words('cool', sample_size=6) # 6 random non-rhymes that sound similar to cool
['cowl', 'coal', 'coil', 'call', 'keel', 'kale']

phonetically_related_words('slimy')
['grimy', 'stymie', 'slammed', 'slammer', 'slim', 'seamy', 'slimy', 'slams', 'slime', 'slam', 'samey', 'semi', 'salami']

phonetically_related_words(['word', 'list'])

print(poem_from_word_list(['crypt', 'lost', 'ghost', 'time']))
laced kept crypts  or  corrupt...   toast?
embossed & most...   corrupt  or  ripped!
riposte...   glossed
        lawsuit!
toast -> tame
    groped & team
        kept.
lawsuit -> glossed cast toast
        rhyme.
ghost time

# Other options
print(poem_from_word_list(['crypt', 'lost', 'ghost', 'time'], lines=3))  # Control the number of lines (defaults to 6)
# The following option makes it so each line uses only the phonetically related words of one input word
print(poem_from_word_list(['crypt', 'lost', 'ghost', 'time'], link_line_to_input_word=True))

```
