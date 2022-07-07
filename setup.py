import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()

setup(
    name="django-dynamic-from-clause",
    version="0.0.2",
    description="Gives the ability to dynamically configure SQL For clause for models. "
                "This give you ability to wrap any sql into models and use ORM features on it.",
    keywords=[
        "Django from",
        "From clause", "Dynamic from clause", "Django table function",
        "Django nested query", "Expression to model", "Wrap queryset"
    ],
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/BezBartek/django-dynamic-from-clause",
    author="Bartłomiej Nowak",
    author_email="n.bartek3762@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=["Django"],
    entry_points={},
)
