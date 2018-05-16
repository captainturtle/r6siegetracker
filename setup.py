from setuptools import setup, find_packages

setup(
    name = 'R6SiegeTracker',
    version = '0.0.1',
    url = 'https://github.com/captainturtle/r6siegetracker',
    author = 'Captain Turtle (TurtleBud)',
    author_email = 'martinknight@yandex.com',
    description = 'Stat tracker for the game Rainbow 6 Siege',
    packages = find_packages(),    
    install_requires = [
        'cryptography',
        'requests'
        ],
)