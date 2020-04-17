import os
import pytest
import numpy as np
import pandas as pd
import networkx as nx
from thoraxe import subexons


@pytest.fixture(scope='module')
def mapk8(request):
    filename = request.module.__file__
    test_dir = os.path.dirname(filename)
    data_dir = os.path.join(test_dir, 'data')
    mapk8_dir = os.path.join(data_dir, 'MAPK8_output', 'thoraxe')
    return {
        'splice_graph': os.path.join(mapk8_dir, 'splice_graph.gml'),
        's_exon_table': os.path.join(mapk8_dir, 's_exon_table.csv'),
        'ases_table': os.path.join(mapk8_dir, 'ases_table.csv'),
        'path_table': os.path.join(mapk8_dir, 'path_table.csv')
    }


def test_ases(mapk8):
    s_exon_df = pd.read_csv(mapk8['s_exon_table'])
    graph = nx.read_gml(mapk8['splice_graph'])
    trx_df = subexons.ases.get_transcript_scores(s_exon_df, graph)
    path_table, ases_df = subexons.ases.conserved_ases(s_exon_df,
                                                       mapk8['splice_graph'])

    assert all(trx_df == path_table)

    assert 'IsHuman' not in trx_df.columns

    select = trx_df.Path == 'start/8_0/1_0/14_0/2_0/4_0/4_1/stop'
    assert all(trx_df.PathGeneNumber[select] == 1)
    assert all(trx_df.MinimumTranscriptWeightedConservation[select] ==
               0.03333333333333333)

    assert list(trx_df.PathGeneNumber) == sorted(trx_df.PathGeneNumber,
                                                 reverse=True)
    common_gene_num = [len(genes.split('/')) for genes in ases_df.CommonGenes]
    assert common_gene_num == sorted(common_gene_num, reverse=True)

    select = np.logical_and(ases_df.CanonicalPath == '7_3/15_0/15_1/stop',
                            ases_df.AlternativePath == '7_3/5_0/stop')
    assert len(ases_df.MutualExclusivity[select]) == 1
    assert all(ases_df.MutualExclusivity[select] == "")
    assert all(ases_df.ASE[select] == "alternative_end")
    select = np.logical_and(ases_df.CanonicalPath == '13_0/7_2',
                            ases_df.AlternativePath == '13_0/9_0/7_2')
    assert not any(select)
    select = np.logical_and(ases_df.CanonicalPath == '4_0/12_1/3_0',
                            ases_df.AlternativePath == '4_0/12_0/3_0')
    assert all(ases_df.MutualExclusivity[select] == "mutually_exclusive")
    assert all(ases_df.ASE[select] == "alternative")
    select = np.logical_and(ases_df.CanonicalPath == '7_3/15_0/15_1/stop',
                            ases_df.AlternativePath == '7_3/7_4/7_5/stop')
    assert all(
        ases_df.MutualExclusivity[select] == "partially_mutually_exclusive")
    assert all(ases_df.ASE[select] == "alternative_end")

    data_path_table = pd.read_csv(mapk8['path_table'])
    data_ases_table = pd.read_csv(mapk8['ases_table'])
    assert sorted(path_table.columns) == sorted(data_path_table.columns)
    assert sorted(ases_df.columns) == sorted(data_ases_table.columns)
    assert path_table.size == data_path_table.size
    assert ases_df.shape[0] == data_ases_table.shape[0]
    for col in [
            'GeneID', 'TranscriptIDCluster', 'TranscriptLength', 'Path',
            'PathGeneNumber'
    ]:
        assert all(path_table[col].values == data_path_table[col].values)
    for col in [  # non-missing and non float columns
            'CanonicalPath', 'AlternativePath', 'ASE', 'CanonicalPathGenes',
            'AlternativePathGenes'
    ]:
        assert all(ases_df[col].values == data_ases_table[col].values)
    for col in [  # float columns
            'CanonicalPathTranscriptWeightedConservation',
            'AlternativePathTranscriptWeightedConservation'
    ]:
        np.isclose(ases_df[col].values,
                   data_ases_table[col].values,
                   rtol=0.0001)
