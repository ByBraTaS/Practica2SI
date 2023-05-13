import json
import matplotlib.pyplot as plt
from sklearn import linear_model
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
        xtest.append([0.0])
    ytest.append([d['peligroso']])

### Creamos el modelo de regresión lineal ###
print("REGRESIÓN LINEAL")
regr = linear_model.LinearRegression()

### Entrenamos el modelo con los datos de train ###
regr.fit(xtrain,ytrain)

### Creamos una predicción utilizando los datos de test ###
ypred = regr.predict(xtest)
print("Error en los datos: %.2f" % mean_squared_error(ytest,ypred))

contadorPeligrosos=0
for i in ypred:
    if i >=0.5:
        contadorPeligrosos+=1

print("Numero de dispositivos peligrosos: ",contadorPeligrosos)

### Mostramos la regresión lineal de la predicción ###
plt.scatter(xtest, ytest, color="black")
plt.plot(xtest, ypred, color="blue", linewidth=3)
plt.xticks(())
plt.yticks(())
plt.show()


