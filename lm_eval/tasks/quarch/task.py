"""
Know What You Don’t Know: Unanswerable Questions for SQuAD
https://arxiv.org/pdf/1806.03822.pdf

Stanford Question Answering Dataset (SQuAD) is a reading comprehension dataset,
consisting of questions posed by crowdworkers on a set of Wikipedia articles,
where the answer to every question is a segment of text, or span, from the
corresponding reading passage, or the question might be unanswerable.
SQuAD2.0 combines the 100,000 questions in SQuAD1.1 with over 50,000 unanswerable
questions written adversarially by crowdworkers to look similar to answerable ones.
To do well on SQuAD2.0, systems must not only answer questions when possible, but
also determine when no answer is supported by the paragraph and abstain from answering.

Homepage: https://rajpurkar.github.io/SQuAD-explorer/
"""
from functools import partial
from math import exp
import os
import json

import datasets
from packaging import version

from lm_eval.api.instance import Instance
from lm_eval.api.task import ConfigurableTask


# _CITATION = """
# @misc{rajpurkar2018know,
#     title={Know What You Don't Know: Unanswerable Questions for SQuAD},
#     author={Pranav Rajpurkar and Robin Jia and Percy Liang},
#     year={2018},
#     eprint={1806.03822},
#     archivePrefix={arXiv},
#     primaryClass={cs.CL}
# }
# """


def _squad_metric(predictions, references):
    squad_metric = datasets.load_metric("squad_v2")
    return squad_metric.compute(predictions=predictions, references=references)


def _squad_agg(key, items):
    predictions, references = zip(*items)

    return _squad_metric(predictions=predictions, references=references).get(key, 0)


class SQuAD2(ConfigurableTask):
    VERSION = 1
    DATASET_PATH = "json"
    DATASET_NAME = None
    DATA_FILES = {"train": "./train.json", "validation": "./test.json"}

    def __init__(self):
        super().__init__(config={"metadata": {"version": self.VERSION}})
        
        # self.dataset = self.load_local_dataset(".")
        

    # HF changed squad on us so we have to make sure we aren't running the old one
    # assert version.parse(datasets.__version__) >= version.parse(
    #     "1.11.0"
    # ), "datasets v1.11.0 or later required for SQuAD"

    # def load_local_dataset(self, data_dir="."):

    #     train_path = os.path.join(data_dir, "train.json")
    #     test_path = os.path.join(data_dir, "test.json")

    #     with open(train_path, "r") as train_file:
    #         train_data = json.load(train_file)

    #     with open(test_path, "r") as test_file:
    #         test_data = json.load(test_file)

    #     return {
    #         "train": train_data,
    #         "validation": test_data
    #     }


    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return True

    def has_test_docs(self):
        return False

    def training_docs(self):
        return self.dataset["train"]

    def validation_docs(self):
        return self.dataset["validation"]

    def doc_to_text(self, doc):
        return (
            "Title: "
            + doc["title"]
            + "\n\n"
            + "Background: "
            + doc["context"]
            + "\n\n"
            + "Question: "
            + doc["question"]
            + "\n\n"
            + "Answer:"
        )

    def should_decontaminate(self):
        return True

    def doc_to_decontamination_query(self, doc):
        return doc["context"]

    def doc_to_target(self, doc):
        answer_list = doc["answers"]["text"]
        if len(answer_list) > 0:
            answer = answer_list[0]
        else:
            answer = "unanswerable"
        return " " + answer

    def construct_requests(self, doc, ctx, **kwargs):
        """Uses RequestFactory to construct Requests and returns an iterable of
        Requests which will be sent to the LM.

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param ctx: str
            The context string, generated by fewshot_context. This includes the natural
            language description, as well as the few shot examples, and the question
            part of the document for `doc`.
        """

        return [
            Instance(
                request_type="generate_until",
                doc=doc,
                arguments=(ctx, {"until": ["\n"]}),
                idx=0,
                **kwargs,
            ),
            Instance(
                request_type="loglikelihood",
                doc=doc,
                arguments=(ctx, " " + "unanswerable"),
                idx=0,
                **kwargs,
            ),
        ]

    def process_results(self, doc, results):
        """Take a single document and the LM results and evaluates, returning a
        dict where keys are the names of submetrics and values are the values of
        the metric for that one document

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param results:
            The results of the requests created in construct_requests.
        """

        continuation, (logprob_unanswerable, _) = results

        no_answer_probability = exp(logprob_unanswerable)

        predictions = {
            "id": doc["id"],
            "prediction_text": continuation,
            "no_answer_probability": no_answer_probability,
        }

        references = {
            "id": doc["id"],
            "answers": doc["answers"]
        }


        return {
            "exact": (
                predictions,
                references,
            ),  # Exact match (the normalized answer exactly match the gold answer)
            "f1": (
                predictions,
                references,
            ),  # The F-score of predicted tokens versus the gold answer
            "HasAns_exact": (
                predictions,
                references,
            ),  # Exact match (the normalized answer exactly match the gold answer)
            "HasAns_f1": (
                predictions,
                references,
            ),  # The F-score of predicted tokens versus the gold answer
            "NoAns_exact": (
                predictions,
                references,
            ),  # Exact match (the normalized answer exactly match the gold answer)
            "NoAns_f1": (
                predictions,
                references,
            ),  # The F-score of predicted tokens versus the gold answer
            "best_exact": (
                predictions,
                references,
            ),  # Best exact match (with varying threshold)
            "best_f1": (predictions, references),  # Best F1 (with varying threshold)
        }

    def aggregation(self):
        """
        :returns: {str: [float] -> float}
            A dictionary where keys are the names of submetrics and values are
            functions that aggregate a list of metrics
        """
        return {
            "exact": partial(
                _squad_agg, "exact"
            ),  # Exact match (the normalized answer exactly match the gold answer)
            "f1": partial(
                _squad_agg, "f1"
            ),  # The F-score of predicted tokens versus the gold answer
            "HasAns_exact": partial(
                _squad_agg, "HasAns_exact"
            ),  # Exact match (the normalized answer exactly match the gold answer)
            "HasAns_f1": partial(
                _squad_agg, "HasAns_f1"
            ),  # The F-score of predicted tokens versus the gold answer
            "NoAns_exact": partial(
                _squad_agg, "NoAns_exact"
            ),  # Exact match (the normalized answer exactly match the gold answer)
            "NoAns_f1": partial(
                _squad_agg, "NoAns_f1"
            ),  # The F-score of predicted tokens versus the gold answer
            "best_exact": partial(
                _squad_agg, "best_exact"
            ),  # Best exact match (with varying threshold)
            "best_f1": partial(
                _squad_agg, "best_f1"
            ),  # Best F1 (with varying threshold)
        }

    def higher_is_better(self):
        """
        :returns: {str: bool}
            A dictionary where keys are the names of submetrics and values are
            whether a higher value of the submetric is better
        """
        return {
            "exact": True,  # Exact match (the normalized answer exactly match the gold answer)
            "f1": True,  # The F-score of predicted tokens versus the gold answer
            "HasAns_exact": True,  # Exact match (the normalized answer exactly match the gold answer)
            "HasAns_f1": True,  # The F-score of predicted tokens versus the gold answer
            "NoAns_exact": True,  # Exact match (the normalized answer exactly match the gold answer)
            "NoAns_f1": True,  # The F-score of predicted tokens versus the gold answer
            "best_exact": True,  # Best exact match (with varying threshold)
            "best_f1": True,  # Best F1 (with varying threshold)
        }
