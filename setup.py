from setuptools import setup

setup(
    name = 'guardian',
    version = '0.1.0',
    description = "Script for checking different services status.",
    author = "Dawid Stanek",
    author_email = 'dawid1stanek@gmail.com',

    include_package_data=True,
    
    packages=['guardian'],
    entry_points={
        'console_scripts': [
            'guardian = guardian.__main__:main'
        ]
    },

    install_requires=[
        'argparse',
        'Jinja2==2.7.2',
        'mailer==0.8.1',
    ]  
)
