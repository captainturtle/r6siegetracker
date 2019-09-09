from setuptools import setup, find_packages

setup(
    name = 'r6siegetracker',
    version = '1.0.0',
    url = 'https://github.com/captainturtle/r6siegetracker',
    author = 'Captain Turtle (TurtleBud)',
    author_email = 'martinknight@yandex.com',
    description = 'Stat tracker for the game Rainbow 6 Siege',
    packages = ['r6siegetracker'],
    license = 'Apache v2.0',
    install_requires = [
        'cryptography',
        'requests'
        ],
)