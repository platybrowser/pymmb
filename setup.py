import runpy
from setuptools import setup, find_packages

version = runpy.run_path("mobie/__version__.py")["__version__"]

# minimal setup script for the mmpb package
setup(
    name="mobie",
    packages=find_packages(exclude=["test"]),
    version=version,
    author="Constantin Pape",
    url="https://github.com/platybrowser/mobie-utils-python",
    license='MIT',
    entry_points={
        "console_scripts": [
            "mobie.add_image_data = mobie.image_data:main",
            "mobie.add_mask = mobie.mask:main",
            "mobie.add_registered_volume = mobie.registration:main",
            "mobie.add_segmentation = mobie.segmentation:main",
            "mobie.add_traces = mobie.traces:main",
            "mobie.migrate_to_mobie = mobie.migration.migrate:main",
            "mobie.migrate_dataset_to_mobie = mobie.migration.migrate_dataset:main",
        ]
    },
)
