from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import export_graphviz
from subprocess import call
import json
from sklearn.metrics import mean_squared_error, r2_score

### Preparamos los datos de entrenamiento ###
with open('../data/devices_IA_clases.json', 'r') as f:
    train = json.load(f)

xtrain = []
ytrain = []
for d in train:
    if d['servicios']!=0:
        xtrain.append([d['servicios_inseguros']/d['servicios']])
    else:
        xtrain.append([0])
    ytrain.append([d['peligroso']])

### Preparamos los datos de test ###
with open('../data/devices_IA_predecir_v2.json', 'r') as f:
    test = json.load(f)

xtest = []
ytest = []
for d in test:
    if d['servicios']!=0:
        xtest.append([d['servicios_inseguros']/d['servicios']])
    else:
        xtest.append([0.0])
    ytest.append([d['peligroso']])

### Creamos el modelo de random forest ###

frst = RandomForestClassifier(max_depth=1, random_state=0, n_estimators=10)

### Entrenamos el modelo con los datos de train ###
frst.fit(xtrain, ytrain)

### Creamos una predicción utilizando los datos de test ###
print("RANDOM FOREST")
ypred=(frst.predict(xtest))
print("Error en los datos: %.2f" % mean_squared_error(ytest,ypred))

contadorPeligrosos=0
for i in ypred:
    if i >=0.5:
        contadorPeligrosos+=1

print("Numero de dispositivos peligrosos: ",contadorPeligrosos)

### Mostramos las agrupaciones ###
for i in range(len(frst.estimators_)):
    estimator = frst.estimators_[i]
    export_graphviz(estimator,
                    out_file='tree.dot',
                    rounded=True, proportion=False,
                    class_names=['noPeligroso', 'peligroso'],
                    precision=2, filled=True)
    call(['dot', '-Tpng', 'tree.dot', '-o', 'tree'+str(i)+'.png', '-Gdpi=600'])
