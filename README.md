# Annotation Software for AirVLN Referring Expression

This is an annotation software applying to AirVLN dataset for annotating referring objects in the instruction for each navigation step.

## Prerequisites

### Environment

Python 3.8 or higher:

- dearpygui
- nltk
- stanfordcorenlp
- opencv-python
- numpy
- matplotlib

> We recommand that using conda create a 3.8 python vitual environment and just run pip install -r requirements.txt in the root path.

### Software Installing

Just run `git clone https://github.com/XIRZC/REAnno.git` for cloning the application repository.

### Data

Preparing the AirVLN dataset which comprises of 25 airsim scenarios which we will provide you with download links.

After downloading 25 scenarios, you can just use `scripts/stsplit.sh` for whole split scene running in the background, or use `scripts/stscene.sh` for single scene running for scene-seperate case. And you must ensure you have `settings` subfolder in the root path.

After running the corresponding scenarios, just use `scripts/save_imgs.sh` for saving the corresponding episodes frames gotten in each navigation position. And you must ensure you have `annotation` subfolder in the root path. And you will get `data/${split}/${scene}/JPEGImages` and `data/${split}/${scene}/expressions.json`.

## Using the software for annotating

Just run `python main.py` in the root path with above prepared conda python vitual environment for launching the softare.

And here are several steps for annotating referring objects list below(w. demonstration pictures):

1.