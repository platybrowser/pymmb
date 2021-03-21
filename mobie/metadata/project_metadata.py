import os
import warnings
from .utils import read_metadata, write_metadata
from ..__version__ import SPEC_VERSION

#
# functionality for reading / writing project.schema.json
#


def create_project_metadata(root):
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "project.json")
    if os.path.exists(path):
        raise RuntimeError(f"Project metadata at {path} already exists")
    metadata = {
        "specVersion": SPEC_VERSION,
        "datasets": []
    }
    write_project_metadata(root,  metadata)


def read_project_metadata(root):
    path = os.path.join(root, "project.json")
    return read_metadata(path)


def write_project_metadata(root, metadata):
    path = os.path.join(root, "project.json")
    write_metadata(path, metadata)


#
# query project for datasets etc.
#


def project_exists(root):
    return os.path.exists(os.path.join(root, "project.json"))


def dataset_exists(root, dataset_name):
    project = read_project_metadata(root)
    return dataset_name in project['datasets']


def add_dataset(root, dataset_name, is_default):
    project = read_project_metadata(root)

    if dataset_name in project['datasets']:
        warnings.warn(f"Dataset {dataset_name} is already present!")
    else:
        project['datasets'].append(dataset_name)

    # if this is the only dataset we set it as default
    if is_default or len(project['datasets']) == 1:
        project['defaultDataset'] = dataset_name

    write_project_metadata(root, project)


def get_datasets(root):
    return read_project_metadata(root)['datasets']