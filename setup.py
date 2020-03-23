from setuptools import setup, find_packages

__author__ = 'Corey Bobco'
__email__ = 'corey.bobco@gmail.com'
__version__ = '0.3.4'


with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'console-menu==0.6.0',
    'Gutenberg==0.8.0',
    'hunspell>=0.5.5',
    'inflect==4.1.0',
    'internetarchive==1.8.5',
    'markovify==0.8.0',
    'nltk==3.4.5',
    'pdf2image==1.12.1',
    'rdflib==4.2.2',
    'pronouncing>=0.2.0',
    'python-datamuse>=1.3.0',
    'spacy>=2.2.3',
    'reportlab>=3.5.26',
    'unittest2==1.1.0',
    'wordfreq>=2.2.2',
]

setup(
    name='generativepoetry',
    version='0.3.4',
    description='A library primarily for procedurally generating visual poems',
    long_description=readme,
    author="Corey Bobco",
    author_email='corey.bobco@gmail.com',
    url='https://github.com/coreybobco/generativepoetry-py',
    packages=[
        'generativepoetry',
    ],
    dependency_links = ['https://github.com/coreybobco/gutenberg_cleaner@master#egg=gutenberg_cleaner'],
    package_dir={'generativepoetry':
                 'generativepoetry'},
    package_data={'generativepoetry': ['data/hate_words.txt', 'data/abbreviations_etc.txt']},
    install_requires=requirements,
    scripts=['bin/generative-poetry-cli'],
    license="MIT",
    zip_safe=True,
    keywords='poetry',
    classifiers=[
        "Development Status :: 3 - Alpha",
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Topic :: Artistic Software",
    ],
    test_suite='tests',
)
