from setuptools import setup, find_packages

setup(
    name="mldb",
    version="1.0",
    description="ML Experiment tracker database facilitation",
    author="Chris Boyle",
    author_email="chris@cmjb.tech",
    packages=find_packages(),
    install_requires=[
        "wheel",
        "numpy",
        "matplotlib",
        "psycopg2",
        "simplejson",
        "syt",
        "scipy",
        "scikit-learn",
    ],
    extras_require=dict(test=["pytest", "torch"], qtui="PySide6"),
)
