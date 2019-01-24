import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="icees-client",
    version="0.0.3",
    author="Colin Curtis, Hao Xu",
    author_email="ckcurtis@renci.org, xuhao@renci.org",
    description="ICEES client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xu-hao/icees-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "certifi==2018.10.15",
        "chardet==3.0.4",
        "idna==2.7",
        "requests==2.20.1",
        "urllib3==1.24.1"
    ]
)
