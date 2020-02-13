# Changelog
All notable changes to this project will be documented in this file.

## [0.2.4]
- Menu tweak

## [0.2.3] 2020-02-12
- Fixed bug relating to package data path

## [0.2.2] 2020-02-12
- Added missing dependencies to setup.py

## [0.2.1] 2020-02-12
- Added console-menu for ease of use
- Added filters for hate words
- Corrected a vs an agreement in poems generated via markov method

## [0.2.0] - 2020-01-13
- Added frequently following word(s) functions
- similar_meaning_words, similar_sounding_words, etc. (plural functions) now also accept list of strings as argument
- Added markov chain algorithm for constructing poem lines
- Added PDF generation methods
- Added more cases to 'too similar'

## [0.1.3] - 2019-08-18
- Added related_rare_word(s) functions.
- Fixed issue where first and second words of poem could be too similar

## [0.1.2] - 2019-07-29
- Fixed readme so example image will show on Pypi

## [0.1.1] - 2019-07-29
### Added
- Added example image to readme.
- Added datamuse_api_max option to phonetically_related_words function.

### [0.1.0]
- Renamed frequently_intratextually_coappearing_word(s) functions to contextually_linked_word(s).
- Defined public api with __all___.
- Revised readme's installation instructions.
- Updated module docstrings, adding further detail and fixing errors.
- Fixed bug where wrong results were being returned when datamuse_api_max set to None.
