"""
1. Get data: Kaggle 'Resume Entities for NER' (or annotate with Doccano / Label Studio).
2. Convert to the format below: (text, {"entities": [(start, end, "LABEL"), ...]})
3. Run: python train_ner.py   then load with spacy.load("models/resume_ner")
"""
import random
import spacy
from spacy.training import Example

TRAIN_DATA = [
    ("John Doe is a Python developer at Google", {"entities": [(0, 8, "NAME"), (14, 20, "SKILL"), (38, 44, "COMPANY")]}),
    # ... add hundreds of annotated examples
]

nlp = spacy.blank("en")
ner = nlp.add_pipe("ner")
for _, ann in TRAIN_DATA:
    for _, _, label in ann["entities"]:
        ner.add_label(label)

optimizer = nlp.begin_training()
for epoch in range(30):
    random.shuffle(TRAIN_DATA)
    losses = {}
    for text, ann in TRAIN_DATA:
        nlp.update([Example.from_dict(nlp.make_doc(text), ann)], sgd=optimizer, drop=0.3, losses=losses)
    print(epoch, losses)

nlp.to_disk("models/resume_ner")