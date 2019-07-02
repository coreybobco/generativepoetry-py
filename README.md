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
```
