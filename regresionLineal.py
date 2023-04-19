import json
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score

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

# Create linear regression object
regr = linear_model.LinearRegression()

# Train the model using the training sets
regr.fit(xtrain,ytrain)
print(regr.coef_)

# Make predictions using the testing set
pred = regr.predict(xtest)
predfinal = []
contadorPeligrosos=0
for i in pred:
    if i >=0.5:
        print(1,end=", ")
        contadorPeligrosos+=1
        predfinal.append(1)
    else:
        print(0,end=", ")
        predfinal.append(0)
print()
print("Numero esperado de dispositivos peligrosos: ",contador)
print("Numero real de dispositivos peligrosos: ",contadorPeligrosos)



# Plot outputs
plt.scatter(xtest, predfinal, color="black")
plt.plot(xtest, pred, color="blue", linewidth=3)
plt.xticks(())
plt.yticks(())
plt.show()
