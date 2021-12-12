import sys
sys.path.append('../')
sys.path.append('../src')
sys.path.append('../scripts')
from os import path
import numpy as np
import matplotlib.pyplot as plt
import argparse
from argparse import ArgumentTypeError
import time
import multiprocessing as mp
import PCoA_analysis as pcoa
import L1_pairwise_unifrac as pairwise1
import L2_pairwise_unifrac as pairwise2
import MetadataWrapper as meta
import averages as avg
import clustering as cluster
import CSVWrapper as CSV
import preprocessing as prep

def generate_total_pcoa(biom_file, tree_file, metadata_file, verbose, threads, intermediate_store, preprocessed_use, unifrac_code, output_file):
	if unifrac_code == 1 or unifrac_code == 2:
		if preprocessed_use and path.exists('intermediate/L1_distance_matrix_intermediate.txt'):
			total_matrix_L1 = CSV.read('intermediate/L1_distance_matrix_intermediate.txt')
			if verbose:
				print('\tSuccessfully retrieved intermediate file for L1 Generate Total PCoA')
		else:
			if verbose and preprocessed_use:
				print('\tWarning: Intermediate selected but not available. Computing pairwise alignments... This may take a while...')
			elif verbose:
				print('\tWarning: Intermediate pairwise alignment computation starting... This may take a while...')
			total_matrix_L1 = pairwise1.Total_Pairwise(biom_file, tree_file)
			if verbose:
				print('\tCompleted pairwise distance matrix computation')
			if intermediate_store:
				if verbose:
					print('\tStoring pairwise alignments...')
				if path.exists('intermediate/L1_distance_matrix_intermediate.txt'):
					os.remove('intermediate/L1_distance_matrix_intermediate.txt')
				for i in range(len(total_matrix_L1)):
					CSV.write('intermediate/L1_distance_matrix_intermediate.txt', total_matrix_L1[i])
				if verbose:
					print('\tL1 pairwise distance matrix stored successfully')
		if verbose:
			print('\tGenerating PCoA...')
		pcoa_out_L1 = pcoa.PCoA_total_from_matrix(total_matrix_L1, biom_file, metadata_file)
		if verbose:
			print('\tGeneration complete. Saving...')
		plt.savefig('images/L1_' + str(output_file) + '.png')
		if verbose:
			print('\tL1 PCoA successfully saved')
	if unifrac_code == 0 or unifrac_code == 1:
		if preprocessed_use and path.exists('intermediate/L2_distance_matrix_intermediate.txt'):
			total_matrix_L2 = CSV.read('intermediate/L2_distance_matrix_intermediate.txt')
			if verbose:
				print('\tSuccessfully retrieved intermediate file for L2 Generate Total PCoA')
		else:
			if verbose and preprocessed_use:
				print('\tWarning: Intermediate selected but not available. Computing pairwise alignments... This may take a while...')
			elif verbose:
				print('\tWarning: Intermediate pairwise alignment computation starting... This may take a while...')
			total_matrix_L2 = pairwise2.Total_Pairwise(biom_file, tree_file)
			if verbose:
				print('\tCompleted pairwise distance matrix computation')
			if intermediate_store:
				if verbose:
					print('\tStoring pairwise alignments...')
				if path.exists('intermediate/L2_distance_matrix_intermediate.txt'):
					os.remove('intermediate/L2_distance_matrix_intermediate.txt')
				for i in range(len(total_matrix_L2)):
					CSV.write('intermediate/L2_distance_matrix_intermediate.txt', total_matrix_L2[i])
				if verbose:
					print('\tL2 pairwise distance matrix stored successfully')
		if verbose:
			print('\tGenerating PCoA...')
		pcoa_out_L2 = pcoa.PCoA_total_from_matrix(total_matrix_L2, biom_file, metadata_file)
		if verbose:
			print('\tGeneration complete. Saving...')
		plt.savefig('images/L2_' + str(output_file) + '.png')
		if verbose:
			print('\tL2 PCoA successfully saved')

def generate_group_pcoa(biom_file, tree_file, metadata_file, tax_file, verbose, threads, intermediate_store, preprocessed_use, unifrac_code, output_file):
	if verbose:
		print('\tExtracting metadata...')
	metadata = meta.extract_metadata(metadata_file)
	sample_groups = []
	groups_temp = list(metadata.values())
	groups = []
	for i in range(len(groups_temp)):
		if groups_temp[i]['body_site'] not in groups:
			groups.append(groups_temp[i]['body_site'])
	group_str = ','.join(groups)
	if verbose:
		print('\tSuccessfully extracted metadata')
	if preprocessed_use and path.exists('intermediate/L1_preprocessed_intermediate.txt') and path.exists('intermediate/L2_preprocessed_intermediate.txt'):
		L1_preprocessed = CSV.read('intermediate/L1_preprocessed_intermediate.txt')
		L2_preprocessed = CSV.read('intermediate/L2_preprocessed_intermediate.txt')
		if verbose:
			print('\tSuccessfully retrieved intermediate file for L1 and L2 Preprocessing')
	else:
		if verbose and preprocessed_use:
			print('\tWarning: Intermediate selected but not available. Starting preprocessing... This may take a while...')
		elif verbose:
			print('\tWarning: Biom preprocessing starting... This may take a while...')
		if intermediate_store:
			if path.exists('intermediate/L1_preprocessed_intermediate.txt'):
				os.remove('intermediate/L1_preprocessed_intermediate.txt')
			if path.exists('intermediate/L2_preprocessed_intermediate.txt'):
				os.remove('intermediate/L2_preprocessed_intermediate.txt')
			L1_preprocessed, L2_preprocessed = prep.generate_preprocessed(biom_file, tree_file, 1, 'intermediate/L1_preprocessed_intermediate.txt', 'intermediate/L2_preprocessed_intermediate.txt')
		else:
			L1_preprocessed, L2_preprocessed = prep.generate_preprocessed(biom_file, tree_file, unifrac_code)
		if verbose:
			print('\tCompleted biom preprocessing matrix computation')
	if unifrac_code == 1 or unifrac_code == 2:
		L1_region_names, L1_tax_arr, L1_group_averages, L1_inverse_pushed, L1_neg_arr, L1_distance_matrix, L1_node_type_group_abundances, L1_pushed_arr = avg.compute_L1_averages(L1_preprocessed, biom_file, tree_file, metadata_file, tax_file, 'reports/' + str(output_file) + '_avg_report.csv', 2)
		pcoa_out_L1 = pcoa.PCoA_group_from_matrix(L1_distance_matrix, biom_file, groups, plot=False)
		plt.savefig('images/out_L1_group_average.png')
	if unifrac_code == 0 or unifrac_code == 1:
		L2_region_names, L2_tax_arr, L2_group_averages, L2_inverse_pushed, L2_neg_arr, L2_distance_matrix, L2_node_type_group_abundances, L2_pushed_arr = avg.compute_L2_averages(L2_preprocessed, biom_file, tree_file, metadata_file, tax_file, 'reports/' + str(output_file) + '_avg_report.csv', 0)
		pcoa_out_L2 = pcoa.PCoA_group_from_matrix(L2_distance_matrix, biom_file, groups, plot=False)
		plt.savefig('images/out_L2_group_average.png')

def generate_clustering_report(biom_file, tree_file, metadata_file, verbose, threads, intermediate_store, preprocessed_use, unifrac_code, output_file):
	num_clusters = meta.extract_num_clusters(metadata_file)
	if unifrac_code == 1 or unifrac_code == 2:
		if preprocessed_use and path.exists('intermediate/L1_distance_matrix_intermediate.txt'):
			total_matrix_L1 = CSV.read('intermediate/L1_distance_matrix_intermediate.txt')
			if verbose:
				print('\tSuccessfully retrieved intermediate file for L1 Generate Total PCoA')
		else:
			if verbose and preprocessed_use:
				print('\tWarning: Intermediate selected but not available. Computing pairwise alignments... This may take a while...')
			elif verbose:
				print('\tWarning: Intermediate pairwise alignment computation starting... This may take a while...')
			total_matrix_L1 = pairwise1.Total_Pairwise(biom_file, tree_file)
			if verbose:
				print('\tCompleted pairwise distance matrix computation')
			if intermediate_store:
				if verbose:
					print('\tStoring pairwise alignments...')
				if path.exists('intermediate/L1_distance_matrix_intermediate.txt'):
					os.remove('intermediate/L1_distance_matrix_intermediate.txt')
				for i in range(len(total_matrix_L1)):
					CSV.write('intermediate/L1_distance_matrix_intermediate.txt', total_matrix_L1[i])
				if verbose:
					print('\tL1 pairwise distance matrix stored successfully')
		if verbose:
			print('\tGenerating Clustering Report...')
		report = cluster.report_clustering(total_matrix_L1, biom_file, metadata_file, num_clusters, False, 1, 'reports/L1_' + str(output_file) + '_clustering.txt')
		if verbose:
			print('\tGeneration complete. Saving...')
		for i in range(len(report)):
			CSV.write('reports/L1_' + str(output_file) + '_clustering.csv', report[i])
		if verbose:
			print('\tL1 clustering successfully saved')
	if unifrac_code == 0 or unifrac_code == 1:
		if preprocessed_use and path.exists('intermediate/L2_distance_matrix_intermediate.txt'):
			total_matrix_L2 = CSV.read('intermediate/L2_distance_matrix_intermediate.txt')
			if verbose:
				print('\tSuccessfully retrieved intermediate file for L2 Generate Total PCoA')
		else:
			if verbose and preprocessed_use:
				print('\tWarning: Intermediate selected but not available. Computing pairwise alignments... This may take a while...')
			elif verbose:
				print('\tWarning: Intermediate pairwise alignment computation starting... This may take a while...')
			total_matrix_L2 = pairwise2.Total_Pairwise(biom_file, tree_file)
			if verbose:
				print('\tCompleted pairwise distance matrix computation')
			if intermediate_store:
				if verbose:
					print('\tStoring pairwise alignments...')
				if path.exists('intermediate/L2_distance_matrix_intermediate.txt'):
					os.remove('intermediate/L2_distance_matrix_intermediate.txt')
				for i in range(len(total_matrix_L2)):
					CSV.write('intermediate/L2_distance_matrix_intermediate.txt', total_matrix_L2[i])
				if verbose:
					print('\tL2 pairwise distance matrix stored successfully')
		if verbose:
			print('\tGenerating Clustering Report...')
		report = cluster.report_clustering(total_matrix_L2, biom_file, metadata_file, num_clusters, False, 2, 'reports/L2_' + str(output_file) + '_clustering.txt')
		if verbose:
			print('\tGeneration complete. Saving...')
		for i in range(len(report)):
			CSV.write('reports/L2_' + str(output_file) + '_clustering.csv', report[i])
		if verbose:
			print('\tL2 clustering successfully saved')

def generate_krona(biom_file, tree_file, metadata_file, tax_file, verbose, threads, intermediate_store, preprocessed_use, unifrac_code, output_file):
	if verbose:
		print('\tExtracting metadata...')
	metadata = meta.extract_metadata(metadata_file)
	sample_groups = []
	groups_temp = list(metadata.values())
	groups = []
	for i in range(len(groups_temp)):
		if groups_temp[i]['body_site'] not in groups:
			groups.append(groups_temp[i]['body_site'])
	group_str = ','.join(groups)
	if verbose:
		print('\tSuccessfully extracted metadata')
	if preprocessed_use and path.exists('intermediate/L1_preprocessed_intermediate.txt') and path.exists('intermediate/L2_preprocessed_intermediate.txt'):
		L1_preprocessed = CSV.read('intermediate/L1_preprocessed_intermediate.txt')
		L2_preprocessed = CSV.read('intermediate/L2_preprocessed_intermediate.txt')
		if verbose:
			print('\tSuccessfully retrieved intermediate file for L1 and L2 Preprocessing')
	else:
		if verbose and preprocessed_use:
			print('\tWarning: Intermediate selected but not available. Starting preprocessing... This may take a while...')
		elif verbose:
			print('\tWarning: Biom preprocessing starting... This may take a while...')
		if intermediate_store:
			if path.exists('intermediate/L1_preprocessed_intermediate.txt'):
				os.remove('intermediate/L1_preprocessed_intermediate.txt')
			if path.exists('intermediate/L2_preprocessed_intermediate.txt'):
				os.remove('intermediate/L2_preprocessed_intermediate.txt')
			L1_preprocessed, L2_preprocessed = prep.generate_preprocessed(biom_file, tree_file, 1, 'intermediate/L1_preprocessed_intermediate.txt', 'intermediate/L2_preprocessed_intermediate.txt')
		else:
			L1_preprocessed, L2_preprocessed = prep.generate_preprocessed(biom_file, tree_file, unifrac_code, 'tmp_L1_preprocessed_intermediate.txt', 'tmp_L2_preprocessed_intermediate.txt')
		if verbose:
			print('\tCompleted biom preprocessing matrix computation')
	if unifrac_code == 1 or unifrac_code == 2:
		if preprocessed_use or intermediate_store:
			L1_region_names, L1_tax_arr, L1_group_averages, L1_inverse_pushed, L1_neg_arr, L1_distance_matrix, L1_node_type_group_abundances = avg.compute_L1_averages('intermediate/L1_preprocessed_intermediate.txt', biom_file, tree_file, metadata_file, tax_file, 'reports/' + str(output_file) + '_avg_report.csv')
		else:
			L1_region_names, L1_tax_arr, L1_group_averages, L1_inverse_pushed, L1_neg_arr, L1_distance_matrix, L1_node_type_group_abundances = avg.compute_L1_averages('tmp_L1_preprocessed_intermediate.txt', biom_file, tree_file, metadata_file, tax_file, 'reports/' + str(output_file) + '_avg_report.csv')
		print(L1_inverse_pushed)
		for name in L1_region_names:
			print(name)
			#tax_abundances = {}
			tax_strs = []
			region_abundance_vector = L1_inverse_pushed[name]
			for i in range(len(region_abundance_vector)):
				node_tax = L1_tax_arr[i].split(';')
				new_node_tax = [str(region_abundance_vector[i])]
				for j in range(len(node_tax)):
					if node_tax[j] != 'root':
						new_node_tax.append(node_tax[j][3:])
					else:
						new_node_tax.append(node_tax[j])
					#if node_tax[j] == 'root' and 'root' in tax_abundances:
					#	tax_abundances['root'] += region_abundance_vector[i]
					#elif node_tax[j] == 'root':
					#	tax_abundances['root'] = region_abundance_vector[i]
					#elif node_tax[j][3:] in tax_abundances:
					#	tax_abundances[node_tax[j][3:]] += region_abundance_vector[i]
					#else:
					#	tax_abundances[node_tax[j][3:]] = region_abundance_vector[i]
				node_tax_str = '\t'.join(new_node_tax)
				tax_strs.append(node_tax_str)
			print(tax_strs)
		#pcoa_out_L1 = pcoa.PCoA_group_from_matrix(L1_distance_matrix, biom_file, groups, plot=False)
		#plt.savefig('images/out_L1_group_average.png')
	if unifrac_code == 0 or unifrac_code == 1:
		if preprocessed_use or intermediate_store:
			L2_region_names, L2_tax_arr, L2_group_averages, L2_inverse_pushed, L2_neg_arr, L2_distance_matrix, L2_node_type_group_abundances = avg.compute_L2_averages('intermediate/L2_preprocessed_intermediate.txt', biom_file, tree_file, metadata_file, tax_file, 'reports/' + str(output_file) + '_avg_report.csv')
		else:
			L2_region_names, L2_tax_arr, L2_group_averages, L2_inverse_pushed, L2_neg_arr, L2_distance_matrix, L2_node_type_group_abundances = avg.compute_L2_averages('tmp_L1_preprocessed_intermediate.txt', biom_file, tree_file, metadata_file, tax_file, 'reports/' + str(output_file) + '_avg_report.csv')
		print(L2_inverse_pushed)
		#pcoa_out_L2 = pcoa.PCoA_group_from_matrix(L2_distance_matrix, biom_file, groups, plot=False)
		#plt.savefig('images/out_L2_group_average.png')
	if path.exists('tmp_L1_preprocessed_intermediate.txt'):
		os.remove('tmp_L1_preprocessed_intermediate.txt')
	if path.exists('tmp_L2_preprocessed_intermediate.txt'):
		os.remove('tmp_L2_preprocessed_intermediate.txt')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description='This script calculates various metrics using L2-UniFrac (or optionally L1 for comparison). '
					'It runs requests E2E without the user needing to perform intermediate steps. ', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-v', '--verbose', action='store_true', help='Print out progress report/timing information')
	
	parser.add_argument('-th', '--threads', type=int, metavar='', help='Number of threads to use',
						default=int(mp.cpu_count()/4))
	
	parser.add_argument('-i', '--intermediate_store', action='store_true', help='Stores intermediate report generation')
	parser.add_argument('-p', '--preprocessed_use', action='store_true', help='Uses intermediate report data to accelerate output')

	parser.add_argument('-bi', '--biom_file', metavar='', help='Biom file: Sample dataset in the BIOM file format')
	parser.add_argument('-tr', '--tree_file', metavar='', help='Tree file: OTU Tree in TREE file format')
	parser.add_argument('-md', '--metadata_file', metavar='', help='Metadata file: Sample names will be the first column and body habitats are the third column, following "OBERON:"')
	parser.add_argument('-tx', '--taxonomy_file', metavar='', help='Taxonomy file: Conversion between Tree Node and Taxonomy')
	
	parser.add_argument('-o', '--out_file', metavar='', help='Generic output file name. Specific requested operations will append tags and filetypes to the end')

	parser.add_argument('-t', '--total_pcoa', action='store_true', help='Compute total PCoA and generate plot')
	parser.add_argument('-g', '--group_pcoa', action='store_true', help='Compute group PCoA averages and generate plot')
	parser.add_argument('-c', '--clustering_report', action='store_true', help='Compute clustering report for distance matrix')
	parser.add_argument('-k', '--krona_averages', action='store_true', help='Compute Krona visualization for each averaged group')
	
	parser.add_argument('-L1', '--L1_UniFrac', action='store_true', help='Compute using L1 UniFrac only')
	parser.add_argument('-U', '--UniFrac', action='store_true', help='Compute using both L1 and L2 UniFrac')

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
	elif args.out_file is None and (args.total_pcoa or args.group_pcoa or args.clustering_report):
		raise Exception('Error: Missing output file subname. Please specify and continue')

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
		generate_total_pcoa(args.biom_file, args.tree_file, args.metadata_file, args.verbose, args.threads, args.intermediate_store, args.preprocessed_use, unifrac_code, args.out_file)
		if args.verbose:
			print('Total PCoA Generation Complete. Total Elapsed Time: ' + str(time.time()-segment_start) + ' seconds')
	if args.group_pcoa:
		segment_start = time.time()
		if args.verbose:
			print('Starting Group PCoA Generation...')
		generate_group_pcoa(args.biom_file, args.tree_file, args.metadata_file, args.taxonomy_file, args.verbose, args.threads, args.intermediate_store, args.preprocessed_use, unifrac_code, args.out_file)
		if args.verbose:
			print('Group PCoA Generation Complete. Total Elapsed Time: ' + str(time.time()-segment_start) + ' seconds')
	if args.clustering_report:
		segment_start = time.time()
		if args.verbose:
			print('Starting Clustering Report Generation...')
		generate_clustering_report(args.biom_file, args.tree_file, args.metadata_file, args.verbose, args.threads, args.intermediate_store, args.preprocessed_use, unifrac_code, args.out_file)
		if args.verbose:
			print('Clustering Report Generation Complete. Total Elapsed Time: ' + str(time.time()-segment_start) + ' seconds')
	if args.krona_averages:
		segment_start = time.time()
		if args.verbose:
			print('Starting Krona Visualization Generation...')
		generate_krona(args.biom_file, args.tree_file, args.metadata_file, args.taxonomy_file, args.verbose, args.threads, args.intermediate_store, args.preprocessed_use, unifrac_code, args.out_file)
		if args.verbose:
			print('Clustering Report Generation Complete. Total Elapsed Time: ' + str(time.time()-segment_start) + ' seconds')
