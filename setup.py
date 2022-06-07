# Copyright © 2022 BAAI. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License")
from setuptools import find_packages, setup

setup(
    name="flagai",
    version="v1.0.1",
    description="FlagAI aims to help researchers and developers to freely train and test large-scale models for NLP tasks.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="BAAI-Open",
    author_email="liuguang@baai.ac.cn",
    url="https://github.com/BAAI-Open/FlagAI",
    packages=find_packages(exclude="tests"),  # same as name
    license="Apache 2.0",
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        'nltk==3.6.7',
        'sentencepiece==0.1.96',
        'boto3==1.21.42',
        'pandas==1.3.5',
        'jieba==0.42.1',
        'scikit-learn==1.0.2',
        'tensorboard==2.9.0',
        'transformers==4.18.0',
        'datasets==2.0.0',
        'setuptools==59.5.0',
        'protobuf==3.20.1',
    ]
)