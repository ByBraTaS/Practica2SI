from sklearn import tree
import graphviz
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
        xtrain.append([0.0])
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
        xtest.append([0])
    ytest.append([d['peligroso']])

### Creamos el modelo de árbol de decisión ###
clf = tree.DecisionTreeClassifier(max_depth=1)

### Entrenamos el modelo con los datos de train ###
clf.fit(xtrain, ytrain)

### Creamos una predicción utilizando los datos de test ###
print("DECISION TREE")
ypred = (clf.predict(xtest))

contadorPeligrosos=0
for i in ypred:
    if i >=0.5:
        contadorPeligrosos+=1

contadorReales = ytest.count([1])

print("Numero de dispositivos peligrosos: ",contadorPeligrosos)
print("Numero de dispositivos reales: ", contadorReales)
error = round(abs((contadorPeligrosos / contadorReales) - 1) * 100, 2)
print("Error en los datos: ", error, "%")

### Mostramos el árbol de decisión ###
dot_data = tree.export_graphviz(clf, out_file=None,
                       feature_names=['porcentage'],
                      class_names=['noPeligroso','peligroso'],
                     filled=True, rounded=True,
                    special_characters=True)
graph = graphviz.Source(dot_data)
graph.render('test.gv', view=True).replace('\\', '/')

