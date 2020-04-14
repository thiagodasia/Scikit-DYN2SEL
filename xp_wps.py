from dyn2sel.apply_dcs import WPSMethod
from skmultiflow.meta import AdaptiveRandomForest, OzaBagging
from skmultiflow.data import SEAGenerator, AGRAWALGenerator, FileStream
from skmultiflow.bayes import NaiveBayes
from skmultiflow.trees import HoeffdingTree
from skmultiflow.evaluation import EvaluatePrequential
from copy import deepcopy

import multiprocessing as mp
from pathos.multiprocessing import ProcessingPool
import multiprocess


generators = [
    # (SEAGenerator(random_state=42), "SEA"),
    # (AGRAWALGenerator(random_state=42), "AGRAWAL"),
    (FileStream("p2.csv"), "P2")]

classifiers = [(AdaptiveRandomForest(n_estimators=10, random_state=42), "ARF_10"),
               (AdaptiveRandomForest(n_estimators=100, random_state=42), "ARF_100"),
               (OzaBagging(base_estimator=HoeffdingTree(), n_estimators=10, random_state=42), "OZA_10_HT"),
               (OzaBagging(base_estimator=HoeffdingTree(), n_estimators=100, random_state=42), "OZA_100_HT"),
               (OzaBagging(base_estimator=NaiveBayes(), n_estimators=10, random_state=42), "OZA_10_NB"),
               (OzaBagging(base_estimator=NaiveBayes(), n_estimators=100, random_state=42), "OZA_100_NB"),
               ]
wps_classifiers = []
sizes = [10, 100] * 3
count = 0
for clf, name in classifiers:
    wps_classifiers.append((WPSMethod(deepcopy(clf),
                                      n_selected=int(sizes[count] * 0.4),
                                      window_size=5000,
                                      metric="accuracy"),
                            "WPS_ACC_" + name)
                           )
    count += 1

count = 0

for clf, name in classifiers:
    wps_classifiers.append((WPSMethod(deepcopy(clf),
                                      n_selected=int(sizes[count] * 0.4),
                                      window_size=5000,
                                      metric="recall"),
                            "WPS_REC_" + name)
                           )
    count += 1

classifiers = classifiers + wps_classifiers

# classifiers = wps_classifiers

args_list = []
for gen in generators:
    for clf in classifiers:
        args_list.append((deepcopy(clf), deepcopy(gen)))


def run(args, sema):
    try:
        clf_args, gen_args = args
        clf, clf_name = clf_args
        gen, gen_name = gen_args
        print("running", clf_name, gen_name)
        gen.prepare_for_use()
        filename = "generator=" + gen_name + "&clf=" + clf_name + ".csv"

        ev = EvaluatePrequential(n_wait=10000, max_samples=100000,
                                 pretrain_size=0,
                                 metrics=["accuracy", "model_size", "running_time"],
                                 output_file="results/" + filename)
        ev.evaluate(stream=gen, model=clf)
        sema.release()
    except:
        sema.release()
        print("error with", clf_name, gen_name)


# p = ProcessingPool(1)
# p.map(run, args_list, chunksize=1)
sem = mp.Semaphore(mp.cpu_count())
for i in args_list:
    p = mp.Process(target=run, args=(i, sem))
    p.start()
    sem.acquire()

# multiprocess.Pool(mp.cpu_count()).map(run, args_list)