from setuptools import setup

setup(
    name='mldb',
    version='1.0',
    description='ML Experiment tracker database facilitation',
    author='Chris Boyle',
    author_email='chris@cmjb.tech',
    packages=['mldb'],
    install_requires=['wheel'],
    requires=['numpy', 'matplotlib', 'psycopg2'],
    extras_require=dict(
        test='pytest'
    )
)
