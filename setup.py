import setuptools

with open("README.md", "r", encoding="utf-8") as handler:
    long_description = handler.read()

setuptools.setup(
    name="job_api",
    version="0.0.1",
    author="William Weiskopf",
    description="A little API for managing a priority job queue.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DArtagan/job_api",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    install_requires=["fastapi"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
