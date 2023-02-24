from collections import defaultdict

import matplotlib.pyplot as plt
from fastcore.xtras import save_pickle
from gptchem.gpt_regressor import GPTRegressor
from gptchem.tuner import Tuner
from loguru import logger
from matbench.bench import MatbenchBenchmark
from matbench.constants import CLF_KEY

logger.enable("gptchem")


import time

import decorator


def retry(howmany, *exception_types, **kwargs):
    timeout = kwargs.get("timeout", 0.0)  # seconds

    @decorator.decorator
    def tryIt(func, *fargs, **fkwargs):
        for _ in range(howmany):
            try:
                return func(*fargs, **fkwargs)
            except exception_types or Exception as e:
                print(e)
                if timeout is not None:
                    time.sleep(timeout)

    return tryIt


@retry(3, timeout=5)
def train_test_fold(task, fold):
    regressor = GPTRegressor(
        task.metadata["target"],
        Tuner(n_epochs=8, learning_rate_multiplier=0.02, wandb_sync=False),
        querier_settings={"max_tokens": 10},
    )
    train_inputs, train_outputs = task.get_train_and_val_data(fold)

    # train and validate your model
    regressor.fit(train_inputs, train_outputs.values)

    # Get testing data
    test_inputs = task.get_test_data(fold, include_target=False)

    # Predict on the testing data
    # Your output should be a pandas series, numpy array, or python iterable
    # where the array elements are floats or bools
    predictions = regressor.predict(test_inputs)

    # Record your data!
    task.record(fold, predictions)
    return predictions


mb = MatbenchBenchmark(
    autoload=True,
    subset=[
        "matbench_expt_gap",
        "matbench_steels",
    ],
)

if __name__ == "__main__":
    predictions = []

    for task in mb.tasks:
        task.load()

        for fold_ind, fold in enumerate(task.folds):
            if task.is_recorded[fold_ind]:
                print(f"Skipping fold {fold_ind} of {task.dataset_name}")
                continue
            pred = train_test_fold(task, fold)
            predictions.append(pred)
            train_inputs, train_outputs = task.get_train_and_val_data(fold)

        print(f"{task.dataset_name}: MAE  {task.scores['mae']['mean']}")

        save_pickle(f"{task.dataset_name}.pkl", predictions)
