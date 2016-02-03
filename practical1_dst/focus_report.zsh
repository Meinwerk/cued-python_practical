#!/usr/bin/zsh
python scripts/baseline.py --dataset dstc2_data --dataroot data --trackfile baseline.json --focus True
python scripts/score.py --dataset dstc2_data --dataroot data --trackfile baseline.json --ontology scripts/config/ontology_dstc2.json --scorefile baseline.score.csv
python scripts/report.py --scorefile baseline.score.csv
