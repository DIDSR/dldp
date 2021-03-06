import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dldp", # Replace with your own username
    version="0.0.1",
    author="Weizhe Li",
    author_email="weizheli@gmail.com",
    description="deep learning in digital pathology",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DIDSR/DeepLearningCamelyon/tree/master/dldp",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
