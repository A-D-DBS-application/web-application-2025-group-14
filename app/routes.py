from flask import Blueprint, request, redirect, url_for, render_template, session
from .models import db, lifecycle, materiaal, zone, item, gebruik

main = Blueprint('main', __name__)

#Bovenstaande code niet aanpassen!!!