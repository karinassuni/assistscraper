from setuptools import setup


setup(
    name='assistscraper',
    description='Library for scraping ASSIST.org',
    license='MIT',
    version='3.2.3',
    author='Karina Antonio',
    author_email='karinafantonio@gmail.com',
    url='https://github.com/karinassuni/assistscraper',
    py_modules=['assistscraper'],
    install_requires=[
        'lxml',
    ],
)
