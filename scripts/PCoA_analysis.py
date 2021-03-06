import sys
sys.path.append('../L2Unifrac')
sys.path.append('../L2Unifrac/src')
sys.path.append('../src')
from os import path
from skbio.stats.ordination import pcoa
import csv
import BiomWrapper as BW
import CSVWrapper as CSV
import MetadataWrapper as meta
import pandas as pd
from skbio import DistanceMatrix
import matplotlib.pyplot as plt
import L2Unifrac as L2U
import averages as avg

# File cheatsheet total (python PCoA_analysis.py 0 L2-UniFrac-Out.csv ../data/47422_otu_table.biom ../data/metadata/P_1928_65684500_raw_meta.txt):
# option:		 
# distance_file: 'L2-UniFrac-Out.csv'
# biom_file:     '../data/47422_otu_table.biom'
# metadata_file: '../data/metadata/P_1928_65684500_raw_meta.txt'

# File cheatsheet groups (python PCoA_analysis.py 1 L2-Group-UniFrac-Out.csv ../data/47422_otu_table.biom ../data/metadata/P_1928_65684500_raw_meta.txt skin,saliva,oral\ cavity,vagina,feces):
# option:		 
# distance_file: 'L2-UniFrac-Out.csv'
# biom_file:     '../data/47422_otu_table.biom'
# metadata_file: '../data/metadata/P_1928_65684500_raw_meta.txt'

def PCoA_total(distance_file, biom_file, metadata_file, plot=True):
	distance_matrix = CSV.read(distance_file)

	sk_distance_matrix = DistanceMatrix(distance_matrix, BW.extract_samples(biom_file))

	metadata = meta.extract_metadata(metadata_file)

	pd_metadata = pd.DataFrame.from_dict(metadata, orient='index')

	result = pcoa(sk_distance_matrix)

	fig = result.plot(df=pd_metadata, column='body_site',
							axis_labels=('PC 1 (' + str(round(result.proportion_explained.iloc[0]*100, 2)) + '%)', 'PC 2 (' + str(round(result.proportion_explained.iloc[1]*100, 2)) + '%)', 'PC 3 (' + str(round(result.proportion_explained.iloc[2]*100, 2)) + '%)'),
							title='Samples colored by body site',
							cmap='Set1', s=50)

	fig.set_size_inches(18.5, 10.5)

	if plot:
		plt.show()
	else:
		return fig

def PCoA_group(distance_file, biom_file, groups, plot=True):
	distance_matrix = CSV.read(distance_file)

	sk_distance_matrix = DistanceMatrix(distance_matrix, [str(i) for i in range(len(groups))])

	metadata = {str(i): {'body_site': groups[i]} for i in range(len(groups))}

	pd_metadata = pd.DataFrame.from_dict(metadata, orient='index')

	result = pcoa(sk_distance_matrix)

	fig = result.plot(df=pd_metadata, column='body_site',
							axis_labels=('PC 1 (' + str(round(result.proportion_explained.iloc[0]*100, 2)) + '%)', 'PC 2 (' + str(round(result.proportion_explained.iloc[1]*100, 2)) + '%)', 'PC 3 (' + str(round(result.proportion_explained.iloc[2]*100, 2)) + '%)'),
							title='Samples colored by body site',
							cmap='Set1', s=50)

	fig.set_size_inches(18.5, 10.5)

	if plot:
		plt.show()
	else:
		return fig

def PCoA_total_from_matrix(distance_matrix, biom_file, metadata_file, plot=False):
	sk_distance_matrix = DistanceMatrix(distance_matrix, BW.extract_samples(biom_file))

	metadata = meta.extract_metadata(metadata_file)

	pd_metadata = pd.DataFrame.from_dict(metadata, orient='index')

	result = pcoa(sk_distance_matrix)

	fig = result.plot(df=pd_metadata, column='body_site',
							axis_labels=('PC 1 (' + str(round(result.proportion_explained.iloc[0]*100, 2)) + '%)', 'PC 2 (' + str(round(result.proportion_explained.iloc[1]*100, 2)) + '%)', 'PC 3 (' + str(round(result.proportion_explained.iloc[2]*100, 2)) + '%)'),
							title='Samples colored by body site',
							cmap='Set1', s=50)

	fig.set_size_inches(18.5, 10.5)

	if plot:
		plt.show()
	else:
		return fig

def PCoA_group_from_matrix(distance_matrix, biom_file, groups, plot=False):
	sk_distance_matrix = DistanceMatrix(distance_matrix, [str(i) for i in range(len(groups))])

	metadata = {str(i): {'body_site': groups[i]} for i in range(len(groups))}

	pd_metadata = pd.DataFrame.from_dict(metadata, orient='index')

	result = pcoa(sk_distance_matrix)

	fig = result.plot(df=pd_metadata, column='body_site',
							axis_labels=('PC 1 (' + str(round(result.proportion_explained.iloc[0]*100, 2)) + '%)', 'PC 2 (' + str(round(result.proportion_explained.iloc[1]*100, 2)) + '%)', 'PC 3 (' + str(round(result.proportion_explained.iloc[2]*100, 2)) + '%)'),
							title='Samples colored by body site',
							cmap='Set1', s=50)

	fig.set_size_inches(18.5, 10.5)

	if plot:
		plt.show()
	else:
		return fig

def PCoA_total_from_matrix_clustering(distance_matrix, biom_file, assignments, plot=False):
	samples = BW.extract_samples(biom_file)
	sk_distance_matrix = DistanceMatrix(distance_matrix, BW.extract_samples(biom_file))

	metadata = {samples[i]: {'body_site': 'Group ' + str(assignments[i]+1)} for i in range(len(assignments))}

	pd_metadata = pd.DataFrame.from_dict(metadata, orient='index')

	result = pcoa(sk_distance_matrix)

	fig = result.plot(df=pd_metadata, column='body_site',
							axis_labels=('PC 1 (' + str(round(result.proportion_explained.iloc[0]*100, 2)) + '%)', 'PC 2 (' + str(round(result.proportion_explained.iloc[1]*100, 2)) + '%)', 'PC 3 (' + str(round(result.proportion_explained.iloc[2]*100, 2)) + '%)'),
							title='Samples colored by body site',
							cmap='Set1', s=50)

	fig.set_size_inches(18.5, 10.5)

	if plot:
		plt.show()
	else:
		return fig

if __name__ == "__main__":
	#PCoA_total('../src/intermediate/L2_distance_matrix_intermediate.txt', '../data/biom/47422_otu_table.biom', '../data/metadata/P_1928_65684500_raw_meta.txt', True)
	region_names, tax_arr, group_averages, inverse_pushed, neg_arr, distance_matrix, node_type_group_abundances = avg.compute_L2_averages('../src/intermediate/L2_preprocessed_intermediate.txt', '../data/biom/47422_otu_table.biom', '../data/trees/gg_13_5_otus_99_annotated.tree', '../data/metadata/P_1928_65684500_raw_meta.txt', '../data/taxonomies/gg_13_8_99.gg.tax', output_file=None)
	PCoA_group_from_matrix(distance_matrix, '../data/biom/47422_otu_table.biom', region_names, True)
	args = sys.argv
	if len(args) != 5 and len(args) != 6:
		raise Exception("Invalid number of parameters.")
	else:
		option = args[1]
		distance_file = args[2]
		biom_file = args[3]
		metadata_file = args[4]
		print(distance_file, biom_file, metadata_file)
		if not path.exists(distance_file) or not path.exists(biom_file) or not path.exists(metadata_file):
			raise Exception("Error: Invalid file path(s).")

		if int(option) == 0:
			PCoA_total(distance_file, biom_file, metadata_file, True)
		elif int(option) == 1:
			body_sites = args[5].split(",")
			PCoA_group(distance_file, biom_file, body_sites, True)
			