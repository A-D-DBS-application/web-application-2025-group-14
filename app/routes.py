from flask import Blueprint, request, redirect, url_for, render_template, session
from .models import db, Material, Zone, Item, Reservation

main = Blueprint('main', __name__)

#Bovenstaande code niet aanpassen!!!

