import sys
sys.path.append('../L2Unifrac')
sys.path.append('../L2Unifrac/src')
sys.path.append('../src')
import L2Unifrac as L2U 
import numpy as np
from scipy.sparse import csc_matrix

try:
    (Tint, lint, nodes_in_order) = L2U.parse_tree_file('../data/old_UniFrac/97_otus_unannotated.tree')
    env_dict = L2U.create_env('../data/old_UniFrac/289_seqs_otus.txt')
except FileNotFoundError:
    (Tint, lint, nodes_in_order) = L2U.parse_tree_file('../data/old_UniFrac/97_otus_unannotated.tree')
    env_dict = L2U.create_env('../data/old_UniFrac/289_seqs_otus.txt')
(env_prob_dict, samples) = L2U.parse_envs(env_dict, nodes_in_order)

#test parse_tree
def test_parse_tree():
    tree_str = '((B:0.1,C:0.2)A:0.3);'
    (Tint1, lint1, nodes_in_order1) = L2U.parse_tree(tree_str)
    assert Tint1 == {0: 2, 1: 2, 2: 3}
    assert lint1 == {(1, 2): 0.1, (2, 3): 0.3, (0, 2): 0.2}
    assert nodes_in_order1 == ['C', 'B', 'A', 'temp0']  # temp0 is the root node

#test push_up and inverse_push_up
def test_inverse():
    #simple tests
    P1 = np.array([0.1, 0.2, 0,  0.3, 0, 0.3, 0.1])
    T1 = {0: 4, 1: 4, 2: 5, 3: 5, 4: 6, 5: 6}
    l1 = {(0, 4): 0.1, (1, 4): 0.1, (2, 5): 0.2, (3, 5): 0, (4, 6): 0.2, (5, 6): 0.2} # 0 edge_length not involving the root
    nodes1 = ['A', 'B', 'C', 'D', 'temp0', 'temp1', 'temp2']
    P_pushed1 = L2U.push_up(P1, T1, l1, nodes1)
    x = np.sqrt(L2U.epsilon) * 0.3
    answer1 = np.array([0.0316227766, 0.0632455532, 0, x, 0.134164079, 0.268328157, 1])
    assert all(np.abs(P_pushed1 - answer1) < 0.00000001) #test push_up
    assert P_pushed1[3] > 10**-18 #P_pushed[3] (edge length 0) is non-zero
    P_inversed1 = L2U.inverse_push_up(P_pushed1, T1, l1, nodes1)
    assert np.sum(abs(P1 - P_inversed1)) < 10**-12 #test inverse_push_up
    l2 = {(0, 4): 0.1, (1, 4): 0.1, (2, 5): 0.2, (3, 5): 0, (4, 6): 0.2, (5, 6): 0} # more than one edge with 0 edge length, involving the root.
    y = np.sqrt(L2U.epsilon) * 0.6
    P_pushed2 = L2U.push_up(P1, T1, l2, nodes1)
    answer2 = np.array([0.0316227766, 0.0632455532, 0, x, 0.134164079, y, 1])
    assert all(np.abs(P_pushed2 - answer2) < 0.00000001)
    #test with real data
    Q = env_prob_dict['232.M2Lsft217']
    Q_pushed = L2U.push_up(Q, Tint, lint, nodes_in_order)
    Q_inversed = L2U.inverse_push_up(Q_pushed, Tint, lint, nodes_in_order)
    assert np.sum(abs(Q - Q_inversed)) < 10**-12

#test if push_up computes the correct unifrac value
def test_push_up():
    tree_str = '((B:0.1,C:0.2)A:0.3);'  # there is an internal node (temp0) here.
    (T1, l1, nodes1) = L2U.parse_tree(tree_str)
    nodes_samples = {
        'C': {'sample1': 1, 'sample2': 0},
        'B': {'sample1': 1, 'sample2': 1},
        'A': {'sample1': 0, 'sample2': 0},
        'temp0': {'sample1': 0, 'sample2': 1}}  # temp0 is the root node
    (nodes_weighted, samples_temp) = L2U.parse_envs(nodes_samples, nodes1)
    unifrac2 = np.linalg.norm(L2U.push_up(nodes_weighted['sample1'], T1, l1, nodes1) -
                  L2U.push_up(nodes_weighted['sample2'], T1, l1, nodes1))
    L2_UniFrac = L2U.L2Unifrac_weighted_plain(T1, l1, nodes1, nodes_weighted['sample1'], nodes_weighted['sample2']) #calculated using L2Unifrac
    print(unifrac2, L2_UniFrac)
    assert np.abs(unifrac2 - L2_UniFrac) < 10**-12

    tree_str = '((B:0.1,C:0.2)A:0.3);'  # there is an internal node (temp0) here.
    (T1, l1, nodes1) = L2U.parse_tree(tree_str)
    nodes_samples = {
        'C': {'sample1': 1, 'sample2': 0},
        'B': {'sample1': 1, 'sample2': 1},
        'A': {'sample1': 1, 'sample2': 0},
        'temp0': {'sample1': 0, 'sample2': 1}}  # temp0 is the root node
    (nodes_weighted, samples_temp) = L2U.parse_envs(nodes_samples, nodes1)
    unifrac2 = np.linalg.norm(L2U.push_up(nodes_weighted['sample1'], T1, l1, nodes1) -
                  L2U.push_up(nodes_weighted['sample2'], T1, l1, nodes1))
    L2_UniFrac = L2U.L2Unifrac_weighted_plain(T1, l1, nodes1, nodes_weighted['sample1'], nodes_weighted['sample2']) #calculated using L2Unifrac
    print(unifrac2, L2_UniFrac)
    assert np.abs(unifrac2 - L2_UniFrac) < 10**-12
    #test with real data
    P = env_prob_dict['232.M9Okey217']
    Q = env_prob_dict['232.M3Indl217']
    unifrac2 = np.linalg.norm(L2U.push_up(P, Tint, lint, nodes_in_order) -
                             L2U.push_up(Q, Tint, lint, nodes_in_order))
    L2_UniFrac2 = L2U.L2Unifrac_weighted_plain(Tint, lint, nodes_in_order, P, Q) #calculated using L2Unifrac
    print(unifrac2, L2_UniFrac2)
    assert np.abs(unifrac2 - L2_UniFrac2) < 10**-12
    #assert np.sum(np.abs(unifrac2 - L2_UniFrac)) < 10**-10

def test_W2():
    tree_str = '((B:0.4,C:0.6)A:1);'  # there is an internal node (temp0) here.
    (T1, l1, nodes1) = L2U.parse_tree(tree_str)
    nodes_samples = {
        'C': {'sample1': 0, 'sample2': 0.5, 'sample3': 0.17},
        'B': {'sample1': 0, 'sample2': 0.33, 'sample3': 0.5},
        'A': {'sample1': 1, 'sample2': 0.17, 'sample3': 0.33},
        'temp0': {'sample1': 0, 'sample2': 0, 'sample3': 0}}  # temp0 is the root node
    (nodes_weighted, samples_temp) = L2U.parse_envs(nodes_samples, nodes1)
    W2 = L2U.build_W2(T1, l1, nodes1)
    push_up_1 = L2U.push_up(nodes_weighted['sample1'], T1, l1, nodes1)
    push_up_2 = L2U.push_up(nodes_weighted['sample2'], T1, l1, nodes1)
    push_up_3 = L2U.push_up(nodes_weighted['sample3'], T1, l1, nodes1)
    w2_sample1 = W2.dot(np.array(nodes_weighted['sample1']))
    w2_sample2 = W2.dot(np.array(nodes_weighted['sample2']))
    w2_sample3 = W2.dot(np.array(nodes_weighted['sample3']))
    assert all(w2_sample1 - push_up_1 < 10**-12)
    assert all(w2_sample2 - push_up_2 < 10**-12)
    assert all(w2_sample3 - push_up_3 < 10**-12)

    inv_W2 = L2U.inverse_W2(csc_matrix(W2))
    inv_push_up_1 = inv_W2.dot(push_up_1)
    inv_push_up_2 = inv_W2.dot(push_up_2)
    inv_push_up_3 = inv_W2.dot(push_up_3)
    assert all(inv_push_up_1 - nodes_weighted['sample1'] < 10**-12)
    assert all(inv_push_up_2 - nodes_weighted['sample2'] < 10**-12)
    assert all(inv_push_up_3 - nodes_weighted['sample3'] < 10**-12)

    #test with real data
    P = env_prob_dict['232.M9Okey217']
    Q = env_prob_dict['232.M3Indl217']
    W2 = L2U.build_W2(Tint, lint, nodes_in_order)
    push_up_1 = L2U.push_up(P, Tint, lint, nodes_in_order)
    push_up_2 = L2U.push_up(Q, Tint, lint, nodes_in_order)
    assert all(W2.dot(np.array(P)) - push_up_1 < 10**-12)
    assert all(W2.dot(np.array(Q)) - push_up_2 < 10**-12)

    # Note: matrix inversions are much more computationally demanding (fastest known O(n^2.3728639) time).
    # This test takes VERY long to compute even with significant computational resources.
    #inv_W2 = L2U.inverse_W2(csc_matrix(W2))
    #inv_push_up_1 = inv_W2.dot(push_up_1)
    #inv_push_up_2 = inv_W2.dot(push_up_2)
    #assert all(inv_push_up_1 - P < 10**-12)
    #assert all(inv_push_up_2 - Q < 10**-12)

def test_summation():
    tree_str1 = '((B:0.1,C:0.2)A:0.3);'  # there is an internal node (temp0) here.
    (T1_1, l1_1, nodes1) = L2U.parse_tree(tree_str1)
    nodes_samples1 = {
        'C': {'sample1': 1, 'sample2': 0},
        'B': {'sample1': 1, 'sample2': 1},
        'A': {'sample1': 0, 'sample2': 0},
        'temp0': {'sample1': 0, 'sample2': 1}}  # temp0 is the root node
    (nodes_weighted1, samples_temp1) = L2U.parse_envs(nodes_samples1, nodes1)
    push_up_1 = L2U.push_up(nodes_weighted1['sample1'], T1_1, l1_1, nodes1)
    push_up_2 = L2U.push_up(nodes_weighted1['sample2'], T1_1, l1_1, nodes1)
    push_up_avg = L2U.mean_of_vectors([push_up_1, push_up_2])
    push_down_avg = L2U.inverse_push_up(push_up_avg, T1_1, l1_1, nodes1)
    assert(1-sum(push_down_avg) < 10**-12)

    tree_str2 = '((B:0.1,C:0.2)A:0.3);'  # there is an internal node (temp0) here.
    (T1_2, l1_2, nodes2) = L2U.parse_tree(tree_str2)
    nodes_samples2 = {
        'C': {'sample1': 1, 'sample2': 0},
        'B': {'sample1': 1, 'sample2': 1},
        'A': {'sample1': 1, 'sample2': 0},
        'temp0': {'sample1': 0, 'sample2': 1}}  # temp0 is the root node
    (nodes_weighted2, samples_temp2) = L2U.parse_envs(nodes_samples2, nodes2)
    push_up_1 = L2U.push_up(nodes_weighted2['sample1'], T1_2, l1_2, nodes2)
    push_up_2 = L2U.push_up(nodes_weighted2['sample2'], T1_2, l1_2, nodes2)
    push_up_avg = L2U.mean_of_vectors([push_up_1, push_up_2])
    push_down_avg = L2U.inverse_push_up(push_up_avg, T1_2, l1_2, nodes2)
    assert(1-sum(push_down_avg) < 10**-12)

    #test with real data
    P1 = env_prob_dict['232.M9Okey217']
    P2 = env_prob_dict['232.M3Indl217']
    P3 = env_prob_dict['232.L3Space217']
    P4 = env_prob_dict['232.M9Vkey217']
    P5 = env_prob_dict['232.M2Jkey217']
    P6 = env_prob_dict['232.M2Mkey217']
    P7 = env_prob_dict['232.M3Rinl217']
    P8 = env_prob_dict['232.M3Midl217']

    push_up_1 = L2U.push_up(P1, Tint, lint, nodes_in_order)
    push_up_2 = L2U.push_up(P2, Tint, lint, nodes_in_order)
    push_up_3 = L2U.push_up(P3, Tint, lint, nodes_in_order)
    push_up_4 = L2U.push_up(P4, Tint, lint, nodes_in_order)
    push_up_5 = L2U.push_up(P5, Tint, lint, nodes_in_order)
    push_up_6 = L2U.push_up(P6, Tint, lint, nodes_in_order)
    push_up_7 = L2U.push_up(P7, Tint, lint, nodes_in_order)
    push_up_8 = L2U.push_up(P8, Tint, lint, nodes_in_order)
    push_up_avg = L2U.mean_of_vectors([push_up_1, push_up_2, push_up_3, push_up_4, push_up_5, push_up_6, push_up_7, push_up_8])
    push_down_avg = L2U.inverse_push_up(push_up_avg, Tint, lint, nodes_in_order)
    assert(1-sum(push_down_avg) < 10**-12)

def test_weighted():
    tree_str = '((B:0.1,C:0.2)A:0.3);'  # there is an internal node (temp0) here.
    (T1, l1, nodes1) = L2U.parse_tree(tree_str)
    nodes_samples = {
        'C': {'sample1': 1, 'sample2': 0},
        'B': {'sample1': 1, 'sample2': 1},
        'A': {'sample1': 0, 'sample2': 0},
        'temp0': {'sample1': 0, 'sample2': 1}}  # temp0 is the root node
    (nodes_weighted, samples_temp) = L2U.parse_envs(nodes_samples, nodes1)
    unifrac2 = L2U.L2Unifrac_weighted_plain(T1, l1, nodes1, nodes_weighted['sample1'], nodes_weighted['sample2'])
    L2_UniFrac, DifferentialAbundance = L2U.L2Unifrac_weighted(T1, l1, nodes1, nodes_weighted['sample1'], nodes_weighted['sample2']) #calculated using L2Unifrac
    print(unifrac2, L2_UniFrac)
    assert np.abs(unifrac2 - L2_UniFrac) < 10**-12

    tree_str = '((B:0.1,C:0.2)A:0.3);'  # there is an internal node (temp0) here.
    (T1, l1, nodes1) = L2U.parse_tree(tree_str)
    nodes_samples = {
        'C': {'sample1': 1, 'sample2': 0},
        'B': {'sample1': 1, 'sample2': 1},
        'A': {'sample1': 1, 'sample2': 0},
        'temp0': {'sample1': 0, 'sample2': 1}}  # temp0 is the root node
    (nodes_weighted, samples_temp) = L2U.parse_envs(nodes_samples, nodes1)
    unifrac2 = L2U.L2Unifrac_weighted_plain(T1, l1, nodes1, nodes_weighted['sample1'], nodes_weighted['sample2'])
    L2_UniFrac, DifferentialAbundance = L2U.L2Unifrac_weighted(T1, l1, nodes1, nodes_weighted['sample1'], nodes_weighted['sample2']) #calculated using L2Unifrac
    print(unifrac2, L2_UniFrac)
    assert np.abs(unifrac2 - L2_UniFrac) < 10**-12

    P = env_prob_dict['232.M9Okey217']
    Q = env_prob_dict['232.M3Indl217']
    unifrac2 = L2U.L2Unifrac_weighted_plain(Tint, lint, nodes_in_order, P, Q)
    L2_UniFrac2, DifferentialAbundance = L2U.L2Unifrac_weighted(Tint, lint, nodes_in_order, P, Q) #calculated using L2Unifrac
    print(unifrac2, L2_UniFrac2)
    assert np.abs(unifrac2 - L2_UniFrac2) < 10**-12
    #L2U.plot_diffab(nodes_in_order, DifferentialAbundance, 'P_label', 'Q_label', plot_zeros=False, thresh=0.0005)

def run_tests():
    test_parse_tree()
    test_inverse()
    test_push_up()
    test_W2()
    test_summation()
    #test_weighted_flow()
    test_weighted()

if __name__ == "__main__":
    run_tests()