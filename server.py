from flask import Flask
from src.TrainSystem import *

app = Flask(__name__)
system = TrainSystem()