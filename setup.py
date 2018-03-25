from distutils.core import setup

setup(
    name='wallet',
    version='0.0.1',
    packages=['wallet'],
    # long_description=open('README.md').read(),
    entry_points={
          'console_scripts': [
              'wallet = wallet.wallet:main'
          ]
      },
)
