from setuptools import setup


setup(
    name='assistscraper',
    description='Library for scraping ASSIST.org',
    license='MIT',
    version='1.0.0',
    author='Karina Antonio',
    author_email='karinafantonio@gmail.com',
    url='https://github.com/karinassuni/assistscraper',
    packages=['assistscraper'],
    install_requires=[
        'lxml',
        'regex',
        'treelib',
    ],
)
