from setuptools import setup

setup(
    name='pandasodf',
    version='0.1',
    author='Diane Trout',
    author_email='diane@ghic.org',
    packages=['pandasodf'],
    install_requires=[
        'pandas',
        'odfpy',
    ],
    test_suite='tests',
)
