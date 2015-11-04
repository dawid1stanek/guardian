from setuptools import setup

setup(
    name='guardian',
    version='0.1.0',
    packages=['guardian'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'guardian = guardian.__main__:main'
        ]
    } 
)
