import json
import os

import luigi
from cluster_tools.statistics import DataStatisticsWorkflow
from cluster_tools.downscaling import DownscalingWorkflow
from cluster_tools.node_labels import NodeLabelWorkflow
from elf.io import open_file
from ..config import write_global_config


def compute_node_labels(seg_path, seg_key,
                        input_path, input_key,
                        tmp_folder, target, max_jobs,
                        ignore_label=None, max_overlap=True):
    task = NodeLabelWorkflow
    config_folder = os.path.join(tmp_folder, 'configs')

    out_path = os.path.join(tmp_folder, 'data.n5')
    out_key = 'node_labels_%s' % prefix

    t = task(tmp_folder=tmp_folder, config_dir=config_folder,
             max_jobs=max_jobs, target=target,
             ws_path=seg_path, ws_key=seg_key,
             input_path=input_path, input_key=input_key,
             output_path=out_path, output_key=out_key,
             prefix=prefix, max_overlap=max_overlap,
             ignore_label=ignore_label)
    ret = luigi.build([t], local_scheduler=True)
    if not ret:
        raise RuntimeError("Node labels for %s" % prefix)

    f = open_file(out_path, 'r')
    ds_out = f[out_key]

    if max_overlap:
        data = ds_out[:]
    else:
        n_chunks = ds_out.number_of_chunks
        data = [ndist.deserializeOverlapChunk(out_path, out_key, (chunk_id,))[0]
                for chunk_id in range(n_chunks)]
        data = {label_id: overlaps
                for chunk_data in data
                for label_id, overlaps in chunk_data.items()}
    return data


def downscale(in_path, in_key, out_path,
              resolution, scale_factors, chunks,
              tmp_folder, target, max_jobs, block_shape,
              library='vigra', library_kwargs=None, metadata_format='bdv.n5'):
    task = DownscalingWorkflow

    block_shape = chunks if block_shape is None else block_shape
    config_dir = os.path.join(tmp_folder, 'configs')
    write_global_config(config_dir, block_shape=block_shape)

    configs = DownscalingWorkflow.get_config()
    conf = configs['copy_volume']
    conf.update({'chunks': chunks})
    with open(os.path.join(config_dir, 'copy_volume.config'), 'w') as f:
        json.dump(conf, f)

    ds_conf = configs['downscaling']
    ds_conf.update({'chunks': chunks, 'library': library})
    if library_kwargs is not None:
        ds_conf.update({'library_kwargs': library_kwargs})
    with open(os.path.join(config_dir, 'downscaling.config'), 'w') as f:
        json.dump(ds_conf, f)

    halos = scale_factors
    metadata_dict = {'resolution': resolution, 'unit': 'micrometer'}

    t = task(tmp_folder=tmp_folder, config_dir=config_dir,
             target=target, max_jobs=max_jobs,
             input_path=in_path, input_key=in_key,
             scale_factors=scale_factors, halos=halos,
             metadata_format=metadata_format, metadata_dict=metadata_dict,
             output_path=out_path)
    ret = luigi.build([t], local_scheduler=True)
    if not ret:
        raise RuntimeError("Downscaling failed")


def compute_max_id(path, key, tmp_folder, target, max_jobs):
    task = DataStatisticsWorkflow

    stat_path = os.path.join(tmp_folder, 'statistics.json')
    t = task(tmp_folder=tmp_folder, config_dir=os.path.join(tmp_folder, 'configs'),
             target=target, max_jobs=max_jobs,
             path=path, key=key, output_path=stat_path)
    ret = luigi.build([t], local_scheduler=True)
    if not ret:
        raise RuntimeError("Computing max id failed")

    with open(stat_path) as f:
        stats = json.load(f)

    return stats['max']


def add_max_id(in_path, in_key, out_path, out_key,
               tmp_folder, target, max_jobs):
    with open_file(out_path, 'r') as f_out:
        ds_out = f_out[out_key]
        if 'maxId' in ds_out.attrs:
            return

    with open_file(in_path, 'r') as f:
        max_id = f[in_key].attrs.get('maxId', None)

    if max_id is None:
        max_id = compute_max_id(out_path, out_key,
                                tmp_folder, target, max_jobs)

    with open_file(out_path, 'a') as f:
        f[out_key].attrs['maxId'] = int(max_id)
