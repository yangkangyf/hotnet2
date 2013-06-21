# -*- coding: iso-8859-1 -*-
import sys
import hnap
import scipy.io
import stats
import hotnet2 as hn
import hnio
import permutations
import json

def parse_args(raw_args):      
    description = "" #TODO
    parser = hnap.HotNetArgParser(description=description, fromfile_prefix_chars='@')

    parser.add_argument('-hof', '--hotnet_output_file', required=True,
                        help='Path to output file produced by runHotnet2.py')
    parser.add_argument('-pgf', '--permutation_genes_file',
                        help='Path to file containing a list of additional genes that can have\
                              permuted heat values assigned to them in permutation tests')
    parser.add_argument('-n', '--num_permutations', type=int, required=True,
                        help='Number of permutation tests to run')
    parser.add_argument('-s', '--cc_start_size', type=int, default=2,
                        help='Smallest connected component size to count')
    parser.add_argument('-l', '--cc_stop_size', type=int, default=10,
                        help='Largest connected component size to count')
    #TODO: fix this so that multithreading default is true
    parser.add_argument('-m', '--multithreaded', default=False, action='store_true',
                        help='Set to 0 to disable running permutation tests in parallel')
                        
    return parser.parse_args(raw_args)

PARAMETERS = "parameters"

def run(args):
    hotnet_output = json.load(open(args.hotnet_output_file))

    infmat = scipy.io.loadmat(hotnet_output[PARAMETERS]["infmat_file"])[hotnet_output[PARAMETERS]["infmat_name"]]  
    infmat_index = hnio.load_index(hotnet_output[PARAMETERS]["infmat_index_file"])

    heat = hnio.load_heat(hotnet_output[PARAMETERS]["heat_file"])

    delta = hotnet_output[PARAMETERS]["delta"]
    sizes = range(args.cc_start_size, args.cc_stop_size+1)
  
    M, gene_index = hn.induce_infmat(infmat, infmat_index, sorted(heat.keys()))
    h = hn.heat_vec(heat, gene_index)
    sim = hn.similarity_matrix(M, h, not hotnet_output[PARAMETERS]["classic"])
    G = hn.weighted_graph(sim, gene_index, delta)

    extra_genes = hnio.load_gene_list(args.permutation_genes_file)

    heat_permutations = permutations.permute_heat(heat, args.num_permutations, extra_genes, args.multithreaded)
    
    #size2counts is dict(size -> list of counts, 1 per permutation)
    sizes2counts = stats.calculate_permuted_cc_counts(infmat, infmat_index, heat_permutations, delta, sizes, not hotnet_output[PARAMETERS]["classic"], args.multithreaded)
    real_counts = stats.num_components_min_size(G, sizes)
    size2real_counts = dict(zip(sizes, real_counts))
    sizes2stats = stats.compute_statistics(size2real_counts, sizes2counts, args.num_permutations)
    
    print json.dumps(sizes2stats, indent=4)

if __name__ == "__main__": 
    run( parse_args(sys.argv[1:]) )