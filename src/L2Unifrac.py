import numpy as np
import matplotlib.pyplot as plt
import dendropy
import sys
import warnings
import heapq
from scipy.sparse import dok_matrix
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import inv
sys.path.append('../tests')

epsilon = sys.float_info.epsilon

def parse_tree(tree_str):
	'''
	(Tint,lint,nodes_in_order) = parse_tree(tree_str)
	This function will parse a newick tree string and return the dictionary of ancestors Tint.
	Tint indexes the nodes by integers, Tint[i] = j means j is the ancestor of i.
	lint is a dictionary returning branch lengths: lint[(i,j)] = w(i,j) the weight of the edge connecting i and j.
	nodes_in_order is a list of the nodes in the input tree_str such that Tint[i]=j means nodes_in_order[j] is an ancestor
	of nodes_in_order[i]. Nodes are labeled from the leaves up.
	'''
	dtree = dendropy.Tree.get(data=tree_str, schema="newick", suppress_internal_node_taxa=False,store_tree_weights=True)
	#Name all the internal nodes
	nodes = dtree.nodes()
	i=0
	for node in nodes:
		if node.taxon == None:
			node.taxon = dendropy.datamodel.taxonmodel.Taxon(label="temp"+str(i))
			i = i+1
	full_nodes_in_order = [item for item in dtree.levelorder_node_iter()]  # i in path from root to j only if i>j
	full_nodes_in_order.reverse()
	nodes_in_order = [item.taxon.label for item in full_nodes_in_order]  # i in path from root to j only if i>j
	Tint = dict()
	lint = dict()
	nodes_to_index = dict(zip(nodes_in_order, range(len(nodes_in_order))))
	for i in range(len(nodes_in_order)):
		node = full_nodes_in_order[i]
		parent = node.parent_node
		if parent != None:
			Tint[i] = nodes_to_index[parent.taxon.label]
			lint[nodes_to_index[node.taxon.label], nodes_to_index[parent.taxon.label]] = node.edge.length
	return (Tint,lint,nodes_in_order)

def parse_tree_file(tree_str_file, suppress_internal_node_taxa=True, suppress_leaf_node_taxa=False):
	'''
	(Tint,lint,nodes_in_order) = parse_tree(tree_str_file)
	This function will parse a newick tree file (in the file given by tree_str_file) and return the dictionary of ancestors Tint.
	Tint indexes the nodes by integers, Tint[i] = j means j is the ancestor of i.
	lint is a dictionary returning branch lengths: lint[i,j] = w(i,j) the weight of the edge connecting i and j.
	nodes_in_order is a list of the nodes in the input tree_str such that T[i]=j means nodes_in_order[j] is an ancestor
	of nodes_in_order[i]. Nodes are labeled from the leaves up.
	'''
	dtree = dendropy.Tree.get(path=tree_str_file, schema="newick",
							suppress_internal_node_taxa=suppress_internal_node_taxa,
							store_tree_weights=True,
							suppress_leaf_node_taxa = suppress_leaf_node_taxa)
	#Name all the internal nodes
	nodes = dtree.nodes()
	i=0
	for node in nodes:
		if node.taxon == None:
			node.taxon = dendropy.datamodel.taxonmodel.Taxon(label="temp"+str(i))
			i = i+1
	full_nodes_in_order = [item for item in dtree.levelorder_node_iter()]  # i in path from root to j only if i>j
	full_nodes_in_order.reverse()
	nodes_in_order = [item.taxon.label for item in full_nodes_in_order]  # i in path from root to j only if i>j
	Tint = dict()
	lint = dict()
	nodes_to_index = dict(zip(nodes_in_order, range(len(nodes_in_order))))
	for i in range(len(nodes_in_order)):
		node = full_nodes_in_order[i]
		parent = node.parent_node
		if parent != None:
			Tint[i] = nodes_to_index[parent.taxon.label]
			if isinstance(node.edge.length, float):
				lint[nodes_to_index[node.taxon.label], nodes_to_index[parent.taxon.label]] = node.edge.length
			else:
				lint[nodes_to_index[node.taxon.label], nodes_to_index[parent.taxon.label]] = 0.0
	return (Tint,lint,nodes_in_order)

# This will return the L2Unifrac distance only
def L2Unifrac_weighted(Tint, lint, nodes_in_order, P, Q, include_tmp_diffab=True):
	'''
	(Z, diffab) = L2Unifrac_weighted(Tint, lint, nodes_in_order, P, Q)
	This function takes the ancestor dictionary Tint, the lengths dictionary lint, the basis nodes_in_order
	and two probability vectors P and Q (typically P = envs_prob_dict[samples[i]], Q = envs_prob_dict[samples[j]]).
	Returns the weighted Unifrac distance Z and the differential abundance. The differential abundance vector diffab 
	is a dictionary with tuple keys using elements of Tint and values diffab[(i, j)] equal to the signed difference 
	of abundance between the two samples restricted to the sub-tree defined by nodes_in_order(i) and weighted by the 
	edge length lint[(i,j)].
	'''
	num_nodes = len(nodes_in_order)
	Z = 0
	diffab = dict()
	partial_sums = P - Q
	for i in range(num_nodes - 1):
		val = partial_sums[i]
		partial_sums[Tint[i]] += val
		if val != 0 and (include_tmp_diffab or nodes_in_order[i][0] != 't'):
			diffab[(i, Tint[i])] = lint[i, Tint[i]]*val # Captures diffab
		Z += lint[i, Tint[i]]*(val**2)
	Z = np.sqrt(Z)
	return (Z, diffab)

def L2Unifrac_weighted_plain(Tint, lint, nodes_in_order, P, Q):
	'''
	Z = L2Unifrac_weighted_plain(ancestors, edge_lengths, nodes_in_order, P, Q)
	This function takes the ancestor dictionary Tint, the lengths dictionary lint, the basis nodes_in_order
	and two probability vectors P and Q (typically P = envs_prob_dict[samples[i]], Q = envs_prob_dict[samples[j]]).
	Returns the weighted Unifrac distance Z.
	'''
	num_nodes = len(nodes_in_order)
	Z = 0
	eps = 1e-8
	partial_sums = P - Q # Vector of partial sums obtained by computing the difference between probabilities of two samples. 
	for i in range(num_nodes - 1):
		val = partial_sums[i]
		if abs(val) > eps:
			partial_sums[Tint[i]] += val
			Z += lint[i, Tint[i]]*(val**2)
	Z = np.sqrt(Z)
	return Z

def push_up(P, Tint, lint, nodes_in_order):
	'''
	P = push_up(P, Tint, lint, nodes_in_order)
	This function takes the ancestor dictionary Tint, the lengths dictionary lint, the basis nodes_in_order
	and the probability vector P.
	Returns the pushed-up probability vector of P with respect to the phylogenetic tree.
	'''
	P_pushed = P + 0  # don't want to stomp on P
	for i in range(len(nodes_in_order) - 1):
		if lint[i, Tint[i]] == 0:
			lint[i, Tint[i]] = epsilon
		P_pushed[Tint[i]] += P_pushed[i]  # push mass up
		P_pushed[i] *= np.sqrt(lint[i, Tint[i]])
	return P_pushed

def build_W2(Tint, lint, nodes_in_order):
	'''
	W2 = build_W2(Tint, lint, nodes_in_order)
	This function takes the ancestor dictionary Tint, the lengths dictionary lint, the basis nodes_in_order.
	Returns the transformation matrix corresponding to the push up operation for use on P probability vectors
	'''
	n = len(nodes_in_order)
	W2 = dok_matrix((n, n), dtype=np.float64)
	for i in range(n):
		cur_node = i
		while cur_node != n:
			if cur_node in Tint:
				W2[cur_node, i] = np.sqrt(lint[cur_node, Tint[cur_node]])
				cur_node = Tint[cur_node]
			else:
				W2[cur_node, i] = 1
				cur_node += 1
	W2 = csr_matrix(W2)
	return W2

def inverse_push_up(P, Tint, lint, nodes_in_order):
	'''
	P = inverse_push_up(P, Tint, lint, nodes_in_order)
	This function takes the ancestor dictionary Tint, the lengths dictionary lint, the basis nodes_in_order
	and the pushed-up probability vector P.
	Returns the probability vector of P with respect to the phylogenetic tree.
	'''
	P_pushed = np.zeros(P.shape)  # don't want to stomp on P
	for i in range(len(nodes_in_order) - 1):
		if lint[i, Tint[i]] == 0:
			edge_length = epsilon
		else:
			edge_length = lint[i, Tint[i]]
		p_val = P[i]
		P_pushed[i] += 1/np.sqrt(edge_length) * p_val  # re-adjust edge lengths
		if P_pushed[i] < epsilon:
			P_pushed[i] = 0
		P_pushed[Tint[i]] -= 1/np.sqrt(edge_length) * p_val  # propagate mass upward, via subtraction, only using immediate descendants
	root = len(nodes_in_order) - 1
	P_pushed[root] += P[root]
	return P_pushed

def inverse_W2(W2):
	'''
	:param W2: an nxn matrix of edge lengths on a tree, where the diagonal corresponds to weights of each node n and all descendents j 
	of n are assigned the same weight at position j in row n.
	:return: the inverse of matrix W2
	'''
	return inv(W2)

def mean_of_vectors(L):
	'''
	:param L: a list of vectors
	:return: a vector with each entry i being the mean of vectors of L at position i
	'''
	return np.mean(L, axis=0)

def plot_diffab(nodes_in_order, taxonomy_in_order, diffab, P_label, Q_label, plot_zeros=True, thresh=0, show=True, maxDisp=0, includeTemp=True):
	'''
	plot_diffab(nodes_in_order, diffab, P_label, Q_label)
	Plots the differential abundance vector.
	:param nodes_in_order: list returned from parse_envs
	:param diffab: differential abundance vector (returned from one flavor of L2Unifrac)
	:param P_label: label corresponding to the sample name for P (e.g. when calling L2Unifrac_weighted(Tint, lint, nodes_in_order, P, Q))
	:param Q_label: label corresponding to the sample name for P (e.g. when calling L2Unifrac_weighted(Tint, lint, nodes_in_order, P, Q))
	:param plot_zeros: flag (either True or False) that specifies if the zero locations should be plotted. Warning, if your tree is large and plot_zeros=True, this can cause a crash.
	:param thresh: only plot those parts of the diffab vector that are above thresh, specify everything else as zero
	:return: None (makes plot)
	'''
	new_tax_in_order = []
	for i in range(len(taxonomy_in_order)):
		new_tax_in_order.append(taxonomy_in_order[i].split(';')[-2:-1][0])

	x = range(len(nodes_in_order))
	y = np.zeros(len(nodes_in_order))
	keys = diffab.keys()
	for key in keys:
		y[key[0]] = diffab[key]

	pos_loc = [x[i] for i in range(len(y)) if (y[i] > thresh and 'temp' not in nodes_in_order[i]) or (y[i] > thresh and includeTemp)]
	neg_loc = [x[i] for i in range(len(y)) if (y[i] < -thresh and 'temp' not in nodes_in_order[i]) or (y[i] < -thresh and includeTemp)]
	zero_loc = [x[i] for i in range(len(y)) if (-thresh <= y[i] <= thresh and 'temp' not in nodes_in_order[i]) or (-thresh <= y[i] <= thresh and includeTemp)]

	pos_val = [y[i] for i in range(len(y)) if (y[i] > thresh and 'temp' not in nodes_in_order[i]) or (y[i] > thresh and includeTemp)]
	neg_val = [y[i] for i in range(len(y)) if (y[i] < -thresh and 'temp' not in nodes_in_order[i]) or (y[i] < -thresh and includeTemp)]
	zero_val = [y[i] for i in range(len(y)) if (-thresh <= y[i] <= thresh and 'temp' not in nodes_in_order[i]) or (-thresh <= y[i] <= thresh and includeTemp)]

	# Increase threshold until pos and neg are less than the max display (very inefficient... TODO: optimize using by taking top 10 or so elements directly)
	while True:
		if (len(pos_val) > maxDisp or len(neg_val) > maxDisp) and maxDisp > 0:
			thresh *= 1.05
		else:
			break

		if len(pos_val) > maxDisp:
			pos_loc = [x[i] for i in range(len(y)) if (y[i] > thresh and 'temp' not in nodes_in_order[i]) or (y[i] > thresh and includeTemp)]
		if len(neg_val) > maxDisp:
			neg_loc = [x[i] for i in range(len(y)) if (y[i] < -thresh and 'temp' not in nodes_in_order[i]) or (y[i] < -thresh and includeTemp)]

		if len(pos_val) > maxDisp:
			pos_val = [y[i] for i in range(len(y)) if (y[i] > thresh and 'temp' not in nodes_in_order[i]) or (y[i] > thresh and includeTemp)]
		if len(neg_val) > maxDisp:
			neg_val = [y[i] for i in range(len(y)) if (y[i] < -thresh and 'temp' not in nodes_in_order[i]) or (y[i] < -thresh and includeTemp)]

	if not pos_loc:
		raise Exception('Threshold too high or max too low! Please change and try again.')
	if not neg_loc:
		raise Exception('Threshold too high or max too low! Please change and try again.')

	# The following is to get the indicies in order. Basically, I iterate down both pos_loc and neg_loc simultaneously
	# and create new lists (pos_loc_adj and neg_loc_adj) that are in the same order as pos_loc and neg_loc, but whose
	# union of indicies is equal to range(len(pos_loc + neg_loc)). Simply to make things pretty
	if plot_zeros:
		pos_loc_adj = pos_loc
		neg_loc_adj = neg_loc
		zero_loc_adj = zero_loc
	else:
		pos_loc_adj = []
		neg_loc_adj = []
		tick_names = []

		# rename the indicies so they are increasing by 1
		pos_ind = 0
		neg_ind = 0
		it = 0
		while pos_ind < len(pos_loc) or neg_ind < len(neg_loc):
			if pos_ind >= len(pos_loc):
				neg_loc_adj.append(it)
				tick_names.append(new_tax_in_order[neg_loc[neg_ind]])
				it += 1
				neg_ind += 1
			elif neg_ind >= len(neg_loc):
				pos_loc_adj.append(it)
				tick_names.append(new_tax_in_order[pos_loc[pos_ind]])
				it += 1
				pos_ind += 1
			elif pos_loc[pos_ind] < neg_loc[neg_ind]:
				pos_loc_adj.append(it)
				tick_names.append(new_tax_in_order[pos_loc[pos_ind]])
				it += 1
				pos_ind += 1
			elif pos_loc[pos_ind] > neg_loc[neg_ind]:
				neg_loc_adj.append(it)
				tick_names.append(new_tax_in_order[neg_loc[neg_ind]])
				it += 1
				neg_ind +=1
			else:
				print('Something went wrong')
				break


	fig, ax = plt.subplots()

	markerline, stemlines, baseline = ax.stem(neg_loc_adj, neg_val)
	plt.setp(baseline, linewidth=1, color='k')
	plt.setp(markerline, color='r')
	plt.setp(stemlines, linewidth=3, color='r')

	markerline, stemlines, baseline = ax.stem(pos_loc_adj, pos_val)
	plt.setp(baseline, linewidth=1, color='k')
	plt.setp(markerline, color='b')
	plt.setp(stemlines, linewidth=3, color='b')

	if plot_zeros:
		markerline, stemlines, baseline = ax.stem(zero_loc, zero_val)
		plt.setp(baseline, linewidth=1, color='k')
		plt.setp(markerline, color='k')
		plt.setp(stemlines, linewidth=3, color='k')

	plt.ylabel('DiffAbund', fontsize=16)
	plt.gcf().subplots_adjust(right=0.93, left=0.15)

	# If you want the zeros plotted, label EVERYTHING, otherwise just label the things that are there...
	if plot_zeros:
		plt.xticks(x, nodes_in_order, rotation='vertical', fontsize=8)
	else:
		plt.xticks(range(len(pos_loc_adj + neg_loc_adj)), tick_names, rotation='vertical', fontsize=8)

	plt.subplots_adjust(bottom=0.35, top=.93)
	plt.text(plt.xticks()[0][-1]+0.1, max(pos_val), P_label, rotation=90, horizontalalignment='center', verticalalignment='top', multialignment='center', color='b', fontsize=14)
	plt.text(plt.xticks()[0][-1]+0.1, min(neg_val), Q_label, rotation=90, horizontalalignment='center', verticalalignment='bottom', multialignment='center', color='r', fontsize=14)
	
	if show:
		plt.show()
	else:
		return fig

def create_env(sample_file):
	'''
	:param sample_file: a file containding ids and samples
	:return: an env_dict in the form of { id: {sample:count} }
	'''
	env_dict = dict()
	with open(sample_file) as fp:
		line = fp.readline()
		while line:
			list = line.split()
			key = list.pop(0) #get key
			env_dict[key] = dict()
			for str in list:
				sample = str.split('_')[0]
				if sample in env_dict[key]:
					env_dict[key][sample] += 1
				else:
					env_dict[key][sample] = 1
			line = fp.readline()
	fp.close()
	return env_dict

def parse_envs(envs, nodes_in_order):
	'''
	(envs_prob_dict, samples) = parse_envs(envs, nodes_in_order)
	This function takes an environment envs and the list of nodes nodes_in_order and will return a dictionary envs_prob_dict
	with keys given by samples. envs_prob_dict[samples[i]] is a probability vector on the basis nodes_in_order denoting for sample i.
	'''
	nodes_in_order_dict = dict(zip(nodes_in_order,range(len(nodes_in_order))))
	for node in envs.keys():
		if node not in nodes_in_order_dict:
			print("Warning: environments contain taxa " + node + " not present in given taxonomic tree. Ignoring")
	envs_prob_dict = dict()
	for i in range(len(nodes_in_order)):
		node = nodes_in_order[i]
		if node in envs:
			samples = envs[node].keys()
			for sample in samples:
				if sample not in envs_prob_dict:
					envs_prob_dict[sample] = np.zeros(len(nodes_in_order))
					envs_prob_dict[sample][i] = envs[node][sample]
				else:
					envs_prob_dict[sample][i] = envs[node][sample]
	#Normalize samples
	samples = envs_prob_dict.keys()
	for sample in samples:
		if envs_prob_dict[sample].sum() == 0:
			warnings.warn("Warning: the sample %s has non-zero counts, do not use for Unifrac calculations" % sample)
		envs_prob_dict[sample] = envs_prob_dict[sample]/envs_prob_dict[sample].sum()
	return (envs_prob_dict, samples)

def run_tests():
	import test_meanUnifrac as test
	test.run_tests()


if __name__ == '__main__':
	run_tests()