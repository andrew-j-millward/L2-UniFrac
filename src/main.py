# The purpose of main.py is to perform all necessary operations using a base set of data.

import sys
sys.path.append('../')
sys.path.append('../src')
sys.path.append('../scripts')
from os import path
import L1Unifrac as L1U
import L2Unifrac as L2U
import BiomWrapper as BW
import CSVWrapper as CSV
import TaxWrapper as tax

import PCoA_analysis as pcoa
import L1_pairwise_unifrac as pairwise1
import L2_pairwise_unifrac as pairwise2
import matplotlib.pyplot as plt
import MetadataWrapper as meta
import averages as avg
import clustering as cluster
import argparse
from argparse import ArgumentTypeError
import multiprocessing as mp
import time

import numpy as np

def generate_total_pcoa(biom_file, tree_file, metadata_file, verbose, threads, intermediate_store, preprocessed_use, unifrac_code):
	if unifrac_code == 1 or unifrac_code == 2:
		total_matrix_L1 = pairwise1.Total_Pairwise(biom_file, tree_file)
		pcoa_out_L1 = pcoa.PCoA_total_from_matrix(total_matrix_L1, biom_file, metadata_file)
		plt.savefig('images/out_L1.png')
	if unifrac_code == 0 or unifrac_code == 1:
		total_matrix_L2 = pairwise2.Total_Pairwise(biom_file, tree_file)
		pcoa_out_L1 = pcoa.PCoA_total_from_matrix(total_matrix_L2, biom_file, metadata_file)
		plt.savefig('images/out_L2.png')

def generate_group_pcoa(biom_file, tree_file, metadata_file, tax_file, verbose, threads, intermediate_store, preprocessed_use, unifrac_code):
	metadata = meta.extract_metadata(metadata_file)
	sample_groups = []
	groups_temp = list(metadata.values())
	groups = []
	for i in range(len(groups_temp)):
		if groups_temp[i]['body_site'] not in groups:
			groups.append(groups_temp[i]['body_site'])
	group_str = ','.join(groups)
	L1_preprocessed, L2_preprocessed = generate_preprocessed(biom_file, tree_file)
	_, _, _, _, _, _, _, _, L1_distance_matrix, L2_distance_matrix, _, _ = avg.compute_averages(L1_preprocessed, L2_preprocessed, biom_file, tree_file, metadata_file, tax_file)
	pcoa_out_L1 = pcoa.PCoA_group_from_matrix(L1_distance_matrix, biom_file, group_str, plot=False)
	plt.savefig('images/out_L1_group_average.png')
	pcoa_out_L2 = pcoa.PCoA_group_from_matrix(L2_distance_matrix, biom_file, group_str, plot=False)
	plt.savefig('images/out_L2_group_average.png')

def generate_clustering_report(biom_file, tree_file, metadata_file, verbose, threads, intermediate_store, preprocessed_use, unifrac_code):
	total_matrix_L1 = pairwise1.Total_Pairwise(biom_file, tree_file)
	total_matrix_L2 = pairwise2.Total_Pairwise(biom_file, tree_file)
	cluster.report_clustering(total_matrix_L1, total_matrix_L2, biom_file, metadata_file, 'reports/clustering_report.txt')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description="This script calculates various metrics using L2-UniFrac (or optionally L1 for comparison). "
					"It runs requests E2E without the user needing to perform intermediate steps. ", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-v', '--verbose', action="store_true", help="Print out progress report/timing information")
	
	parser.add_argument('-th', '--threads', type=int, metavar='', help="Number of threads to use",
						default=int(mp.cpu_count()/4))
	
	parser.add_argument('-i', '--intermediate_store', action="store_true", help="Stores intermediate report generation")
	parser.add_argument('-p', '--preprocessed_use', action="store_true", help="Uses intermediate report data to accelerate output")

	parser.add_argument('-bi', '--biom_file', metavar='', help="Biom file: Sample dataset in the BIOM file format")
	parser.add_argument('-tr', '--tree_file', metavar='', help="Tree file: OTU Tree in TREE file format")
	parser.add_argument('-md', '--metadata_file', metavar='', help="Metadata file: Sample names will be the first column and body habitats are the third column, following 'OBERON:'")
	parser.add_argument('-tx', '--taxonomy_file', metavar='', help="Taxonomy file: Conversion between Tree Node and Taxonomy")
	
	parser.add_argument('-o', '--out_file', metavar='', help='Generic output file name. Specific requested operations will append tags and filetypes to the end')

	parser.add_argument('-t', '--total_pcoa', action="store_true", help='Compute total PCoA and generate plot')
	parser.add_argument('-g', '--group_pcoa', action="store_true", help='Compute group PCoA averages and generate plot')
	parser.add_argument('-c', '--clustering_report', action="store_true", help='Compute clustering report for distance matrix')
	
	parser.add_argument('-L1', '--L1_UniFrac', action="store_true", help='Compute using L1 UniFrac only')
	parser.add_argument('-U', '--UniFrac', action="store_true", help='Compute using both L1 and L2 UniFrac')

	#generate_group_pcoa('../data/47422_otu_table.biom', '../data/trees/gg_13_5_otus_99_annotated.tree', '../data/metadata/P_1928_65684500_raw_meta.txt', '../data/taxonomies/gg_13_8_99.gg.tax')
	#generate_total_pcoa('../data/47422_otu_table.biom', '../data/trees/gg_13_5_otus_99_annotated.tree', '../data/metadata/P_1928_65684500_raw_meta.txt')

	start = time.time()
	args = parser.parse_args()
	print(args)

	if ((isinstance(args.biom_file, str) and not path.exists(args.biom_file)) or args.biom_file is None) and (args.total_pcoa or args.group_pcoa or args.clustering_report):
		raise Exception('Error: Invalid Biom File Path')
	elif ((isinstance(args.tree_file, str) and not path.exists(args.tree_file)) or args.tree_file is None) and (args.total_pcoa or args.group_pcoa or args.clustering_report):
		raise Exception('Error: Invalid Tree File Path')
	elif ((isinstance(args.metadata_file, str) and not path.exists(args.metadata_file)) or args.metadata_file is None) and (args.total_pcoa or args.group_pcoa or args.clustering_report):
		raise Exception('Error: Invalid Metadata File Path')
	elif ((isinstance(args.taxonomy_file, str) and not path.exists(args.taxonomy_file)) or args.taxonomy_file is None) and (args.group_pcoa):
		raise Exception('Error: Invalid Taxonomy File Path')

	unifrac_code = 0
	if args.UniFrac:
		unifrac_code = 1
	elif args.L1_UniFrac:
		unifrac_code = 2

	if path.exists(args.out_file) and args.verbose:
		print('Output file already exists... It will be overwritten.')

	if args.total_pcoa:
		segment_start = time.time()
		if args.verbose:
			print('Starting Total PCoA Generation...')
		generate_total_pcoa(args.biom_file, args.tree_file, args.metadata_file, args.verbose, args.threads, args.intermediate_store, args.preprocessed_use, unifrac_code)
		if args.verbose:
			print('Total PCoA Generation Complete. Total Elapsed Time: ' + str(time.time()-segment_start))
	if args.group_pcoa:
		segment_start = time.time()
		if args.verbose:
			print('Starting Group PCoA Generation...')
		generate_group_pcoa(args.biom_file, args.tree_file, args.metadata_file, args.taxonomy_file, args.verbose, args.threads, args.intermediate_store, args.preprocessed_use, unifrac_code)
		if args.verbose:
			print('Group PCoA Generation Complete. Total Elapsed Time: ' + str(time.time()-segment_start))
	if args.clustering_report:
		segment_start = time.time()
		if args.verbose:
			print('Starting Clustering Report Generation...')
		generate_clustering_report(args.biom_file, args.tree_file, args.metadata_file, args.verbose, args.threads, args.intermediate_store, args.preprocessed_use, unifrac_code)
		if args.verbose:
			print('Clustering Report Generation Complete. Total Elapsed Time: ' + str(time.time()-segment_start))