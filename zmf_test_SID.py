from os.path import join
from options.eld.base_options import BaseOptions 
from engine import Engine
import torch
import torch.backends.cudnn as cudnn
import data.sid_dataset as datasets
import util.util as util
import data
import glob
import os
import socket

opt = BaseOptions().parse()

cudnn.benchmark = True

if opt.debug:
    opt.display_freq = 20
    opt.print_freq = 20
    opt.nEpochs = 40
    opt.max_dataset_size = 10
    opt.no_log = False
    opt.nThreads = 0
    opt.decay_iter = 0
    opt.serial_batches = True
    opt.no_flip = True


expo_ratio = [100, 250, 300]

if socket.gethostname() == 'HP':
    datadir = '../../data/dataset/SID/Sony/Sony/'
else:
    datadir = '../../data/dataset/SID/Sony/Sony/'


read_expo_ratio = lambda x: float(x.split('_')[-1][:-5])

train_fns = data.read_paired_fns('./data/Sony_train.txt')
eval_fns = data.read_paired_fns('./data/Sony_val.txt')
test_fns = data.read_paired_fns('./data/Sony_test.txt')


eval_fns_list = [[fn for fn in eval_fns if min(int(read_expo_ratio(fn[1])/read_expo_ratio(fn[0])), 300)==ratio] for ratio in expo_ratio]
test_fns_list = [[fn for fn in test_fns if min(int(read_expo_ratio(fn[1])/read_expo_ratio(fn[0])), 300)==ratio] for ratio in expo_ratio]
eval_fns_list = [lst_1 + lst_2 for lst_1, lst_2 in zip(eval_fns_list, test_fns_list)]


# evaluate 15 indoor scenes (but you can also evaluate the performance on the whole dataset)
indoor_ids = data.read_paired_fns('./SID_Sony_15_paired.txt')
eval_fns_list = [[(fn[0], fn[1]) for fn in indoor_ids if int(fn[2]) == ratio] for ratio in expo_ratio]


eval_datasets = [datasets.SIDDataset(datadir, fns, memorize=False, size=None, augment=False, stage_in=opt.stage_in, stage_out=opt.stage_out) for fns in eval_fns_list]


eval_dataloaders = [torch.utils.data.DataLoader(
    eval_dataset, batch_size=1, shuffle=False,
    num_workers=opt.nThreads, pin_memory=True) for eval_dataset in eval_datasets]


"""Main Loop"""
engine = Engine(opt)

for ratio, dataloader in zip(expo_ratio, eval_dataloaders):
    print('Eval ratio {}'.format(ratio))

    # Notice for SID dataset, we only evaluate the quantitative results based on the center 512x512 image regions (Enabled by 'crop=True')
    # since we observe some fixed pattern noise appeared at the bottom corner of some pictures.
    # We don't find such noise pattern in our ELD dataset (SonyA7S2 set), which uses the same camera model as SID dataset.
    # As a result, we conjecture this fixed noise pattern might be caused by lens damage, which should be excluded in evaluation.
    engine.eval(dataloader, dataset_name='sid_eval_{}'.format(ratio), savedir='../../workplace/eld_test', correct=True, crop=True)
