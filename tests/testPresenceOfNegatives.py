import sys
sys.path.append('../L2Unifrac')
sys.path.append('../L2Unifrac/src')
sys.path.append('../src')
import L2Unifrac as L2U
import numpy as np

try:
		(Tint, lint, nodes_in_order) = L2U.parse_tree_file('../data/97_otus_unannotated.tree')
		env_dict = L2U.create_env('../data/289_seqs_otus.txt')
except FileNotFoundError:
		(Tint, lint, nodes_in_order) = L2U.parse_tree_file('../data/97_otus_unannotated.tree')
		env_dict = L2U.create_env('../data/289_seqs_otus.txt')
(env_prob_dict, samples) = L2U.parse_envs(env_dict, nodes_in_order)

def test_median(Ps, Tint, lint, nodes_in_order): #take a list of vectors, push up, take median, then push down
		Ps_pushed = []
		for P in Ps:
				P_pushed = L2U.push_up(P, Tint, lint, nodes_in_order)
				Ps_pushed.append(P_pushed)
		median = L2U.mean_of_vectors(Ps_pushed)
		median_inverse = L2U.inverse_push_up(median, Tint, lint, nodes_in_order)
		print (np.sum(median_inverse < 0))
		return np.any(median_inverse < 0)

is_negative = []
num_its = 1
for num_vectors in range(3, len(samples), 5):
		print (num_vectors)
		for i in range(num_its):
				selected_samples = np.random.choice(list(samples), num_vectors, replace=False)
				Ps = []
				for sample in selected_samples:
						Ps.append(env_prob_dict[sample])
				is_negative.append(test_median(Ps, Tint, lint, nodes_in_order))

print (np.sum(is_negative))
print (np.sum(is_negative)/(len(is_negative)))