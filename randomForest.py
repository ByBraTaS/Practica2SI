from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import export_graphviz
from sklearn.datasets import load_iris
from subprocess import call
import graphviz #https://graphviz.org/download/
import json


# Load training data from JSON file
with open('data/devices_IA_clases.json', 'r') as f:
    train = json.load(f)

xtrain = []
ytrain = []
contador =0
for d in train:
    if d['servicios']!=0:
        xtrain.append([d['servicios_inseguros']/d['servicios']])
    else:
        xtrain.append([0])
    ytrain.append([d['peligroso']])  # replace with the appropriate variable name
    if d['peligroso']==1:
        contador+=1

# Load test data from JSON file
with open('data/devices_IA_predecir.json', 'r') as f:
    test = json.load(f)

xtest = []
for d in test:
    if d['servicios']!=0:
        xtest.append([d['servicios_inseguros']/d['servicios']])
    else:
        xtest.append([0])

clf = RandomForestClassifier(max_depth=2, random_state=0,n_estimators=35)
clf.fit(xtrain, ytrain)
pred=clf.predict(xtest)

contadorPeligrosos = 0
for i in pred:
    if i >= 0.5:
        print(1, end=", ")
        contadorPeligrosos += 1
    else:
        print(0, end=", ")
print()
print("Numero esperado de dispositivos peligrosos: ", contador)
print("Numero real de dispositivos peligrosos: ", contadorPeligrosos)