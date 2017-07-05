from setuptools import setup


setup(
    name='assistscraper',
    description='Library for scraping ASSIST.org',
    license='MIT',
    version='2.0.1',
    author='Karina Antonio',
    author_email='karinafantonio@gmail.com',
    url='https://github.com/karinassuni/assistscraper',
    py_modules=['assistscraper'],
    install_requires=[
        'lxml',
        'regex',
    ],
)
