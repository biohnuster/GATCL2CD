# -*- coding:utf-8 -*-
# @Date : 2022/3/26 21:04
# @Author : Yang Cheng
# @Description : utils.py
# @Software: PyCharm

import numpy as np
import torch
import dgl
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore", message="DGLGraph\.__len__")

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def build_heterograph(circrna_disease_matrix, circSimi, disSimi):
    # for circRNA->adj
    matAdj_circ = np.where(circSimi > 0.5, 1, 0)

    # for disease->adj
    matAdj_dis = np.where(disSimi > 0.5, 1, 0)

    # Heterogeneous adjacency matrix
    h_adjmat_1 = np.hstack((matAdj_circ, circrna_disease_matrix))
    h_adjmat_2 = np.hstack((circrna_disease_matrix.transpose(), matAdj_dis))
    Heterogeneous = np.vstack((h_adjmat_1, h_adjmat_2))

    # heterograph
    g = dgl.heterograph(
        data_dict={
            ('circRNA_disease', 'interaction', 'circRNA_disease'): Heterogeneous.nonzero()},
        num_nodes_dict={
            'circRNA_disease': 718
        })
    return g


# def train_features_choose(rel_adj_mat, features_embedding):
#     rna_nums = rel_adj_mat.size()[0]
#     features_embedding_rna = features_embedding[0:rna_nums, :]
#     features_embedding_dis = features_embedding[rna_nums:features_embedding.size()[0], :]
#     train_features_input, train_lable = [], []
#     # positive position index
#     positive_index_tuple = np.where(rel_adj_mat == 1)
#     positive_index_list = list(zip(positive_index_tuple[0], positive_index_tuple[1]))
#     for (r, d) in positive_index_list:
#         # positive samples
#         train_features_input.append((features_embedding_rna[r, :] * features_embedding_dis[d, :]).unsqueeze(0))
#         train_lable.append(1)
#         # negative samples
#         j = np.random.randint(rel_adj_mat.size()[1])
#         while (r, j) in positive_index_list:
#             j = np.random.randint(rel_adj_mat.size()[1])
#         train_features_input.append((features_embedding_rna[r, :] * features_embedding_dis[j, :]).unsqueeze(0))
#         train_lable.append(0)
#     train_features_input = torch.cat(train_features_input, dim=0)
#     train_lable = torch.FloatTensor(np.array(train_lable)).unsqueeze(1)
#     return train_features_input.to(device), train_lable.to(device)

def train_features_choose(rel_adj_mat, features_embedding, negative_sample_times):
    rna_nums = rel_adj_mat.size()[0]
    features_embedding_rna = features_embedding[0:rna_nums, :]
    features_embedding_dis = features_embedding[rna_nums:features_embedding.size()[0], :]
    train_features_input, train_lable = [], []
    # positive position index
    positive_index_tuple = torch.where(rel_adj_mat == 1)
    positive_index_list = list(zip(positive_index_tuple[0], positive_index_tuple[1]))

    for (r, d) in positive_index_list:
        # positive samples
        train_features_input.append((features_embedding_rna[r, :] * features_embedding_dis[d, :]).unsqueeze(0))
        train_lable.append(1)
        # negative samples
        negative_colindex_list = []
        for i in range(negative_sample_times):
            j = np.random.randint(rel_adj_mat.size()[1])
            while (r, j) in positive_index_list:
                j = np.random.randint(rel_adj_mat.size()[1])
            negative_colindex_list.append(j)
        for nums_1 in range(len(negative_colindex_list)):
            train_features_input.append(
                (features_embedding_rna[r, :] * features_embedding_dis[negative_colindex_list[nums_1], :]).unsqueeze(0))
        for nums_2 in range(len(negative_colindex_list)):
            train_lable.append(0)
    train_features_input = torch.cat(train_features_input, dim=0)
    train_lable = torch.FloatTensor(np.array(train_lable)).unsqueeze(1)
    return train_features_input.to(device), train_lable.to(device)


# if __name__ == '__main__':
#     A = np.loadtxt(r'F:\pycharmspace\pycharm-project\2022_shengxin_code\GATMFCDA\data2\m-d.txt', delimiter=',')
#     circSimi = np.loadtxt(r'F:\pycharmspace\pycharm-project\2022_shengxin_code\GATMFCDA\data2\m-m.txt', delimiter=',')
#     disSimi = np.loadtxt(r'F:\pycharmspace\pycharm-project\2022_shengxin_code\GATMFCDA\data2\d-d.txt', delimiter=',')
#
#     A = torch.from_numpy(A).to(torch.float32)
#     circSimi_mat = torch.from_numpy(circSimi).to(torch.float32)
#     disSimi_mat = torch.from_numpy(disSimi).to(torch.float32)
#     embedding = torch.rand((878, 3)).to(torch.float32)
#     train_features_input, train_lable = train_features_choose(A, embedding, 2)
#     train_lable_out = train_lable
#     for data in train_lable_out:
#         print(data)


def test_features_choose(rel_adj_mat, features_embedding):
    rna_nums, dis_nums = rel_adj_mat.size()[0], rel_adj_mat.size()[1]
    features_embedding_rna = features_embedding[0:rna_nums, :]
    features_embedding_dis = features_embedding[rna_nums:features_embedding.size()[0], :]
    test_features_input, test_lable = [], []

    for i in range(rna_nums):
        for j in range(dis_nums):
            test_features_input.append((features_embedding_rna[i, :] * features_embedding_dis[j, :]).unsqueeze(0))
            test_lable.append(rel_adj_mat[i, j])

    test_features_input = torch.cat(test_features_input, dim=0)
    test_lable = torch.FloatTensor(np.array(test_lable)).unsqueeze(1)
    return test_features_input.to(device), test_lable.to(device)


def sort_matrix(score_matrix, interact_matrix):
    '''
    ??????????????????????????????????????????
    1???np.argsort(data,axis=0)??????????????????????????????
    2???np.argsort(data,axis=1)??????????????????????????????
    '''
    sort_index = np.argsort(-score_matrix, axis=0)  # ???????????????(??????)?????????????????????
    score_sorted = np.zeros(score_matrix.shape)
    y_sorted = np.zeros(interact_matrix.shape)
    for i in range(interact_matrix.shape[1]):
        score_sorted[:, i] = score_matrix[:, i][sort_index[:, i]]
        y_sorted[:, i] = interact_matrix[:, i][sort_index[:, i]]
    return y_sorted, score_sorted


# ???????????????
def GKL(data):
    # circ-disea????????????
    circR_disease = np.array(data)
    m, n = np.shape(circR_disease)

    # ??????circ??????
    normValueList_C = []
    for i in range(m):
        temp = np.linalg.norm(circR_disease[i], ord=2)
        normValueList_C.append(temp * temp)
    segamac = m / (np.sum(normValueList_C))

    # ??????dise??????
    normValueList_D = []
    for j in range(n):
        tempd = np.linalg.norm(circR_disease[:, j], ord=2)
        normValueList_D.append(tempd * tempd)
    segamad = n / (np.sum(normValueList_D))

    # circRNA???????????????????????????
    cicRNA_result = np.zeros((m, m))
    for i in range(m):
        for j in range(m):
            tempcirc = np.linalg.norm(circR_disease[i] - circR_disease[j], ord=2)
            cicRNA_result[i][j] = np.exp(-segamac * (tempcirc * tempcirc))

    # ??????disease???????????????????????????
    disease_result = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            tempdisea = np.linalg.norm(circR_disease[:, i] - circR_disease[:, j], ord=2)
            disease_result[i][j] = np.exp(-segamad * (tempdisea * tempdisea))
    return cicRNA_result, disease_result


# ???????????? validation
def draw_alone_validation_roc_line(tpr_arr_matrix, fpr_arr_matrix):
    # ???????????????????????????
    handlist = []

    # ???????????????????????????????????????????????????
    font2 = {'family': 'Arial',
             'weight': 'normal',
             'size': 18,
             }
    # ????????????????????????????????????????????????
    font1 = {'family': 'Arial',
             'weight': 'normal',
             'size': 15,
             }

    # ?????????????????????figsize??????????????????
    figsize = 12, 9
    figure, ax = plt.subplots(figsize=figsize)
    for row in range(tpr_arr_matrix.shape[0]):
        data_tpr, data_fpr = tpr_arr_matrix[row, :], fpr_arr_matrix[row, :]
        roc_auc = np.trapz(data_tpr, data_fpr)

        b, = plt.plot(data_fpr, data_tpr, label='ROC fold{} (AUC={})'.format(row + 1, round(roc_auc, 4)),
                      linewidth=2)
        handlist.append(b)

    plt.legend(handles=handlist, prop=font1, loc='lower right')

    plt.title('Receiver Operating Characteristic curve: 5-Fold CV', font2)
    plt.xlabel('False positive rate, (1-Specificity)', font2)
    plt.ylabel('True positive rate, (Sensitivity)', font2)

    # ??????????????????????????????????????????????????????
    plt.tick_params(labelsize=18)
    labels = ax.get_xticklabels() + ax.get_yticklabels()
    [label.set_fontname('Arial') for label in labels]

    plt.show()  # ????????????
