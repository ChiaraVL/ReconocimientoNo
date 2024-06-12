# Importaciones necesarias
from sklearn import metrics
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, label_binarize
from joblib import dump
from sklearn.datasets import fetch_openml
from sklearn.utils import check_random_state
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import numpy as np

# Función para obtener los datos
def fetch_data(test_size=10000, randomize=False, standardize=True):
    """
    Obtiene el conjunto de datos MNIST desde OpenML, opcionalmente lo randomiza, lo divide en conjuntos de entrenamiento y prueba,
    y estandariza las características si se especifica.

    Parámetros:
    -----------
    test_size : int, opcional, por defecto=10000
        El número de muestras a incluir en el conjunto de prueba. El conjunto de entrenamiento contendrá las muestras restantes.

    randomize : bool, opcional, por defecto=False
        Si es True, randomiza el orden de las muestras antes de dividir en conjuntos de entrenamiento y prueba.

    standardize : bool, opcional, por defecto=True
        Si es True, estandariza las características eliminando la media y escalando a varianza unitaria.

    Retorna:
    --------
    X_train : array-like, shape (n_train_samples, n_features)
        Las muestras de entrada para el entrenamiento.

    y_train : array-like, shape (n_train_samples,)
        Los valores objetivo para el entrenamiento.

    X_test : array-like, shape (n_test_samples, n_features)
        Las muestras de entrada para la prueba.

    y_test : array-like, shape (n_test_samples,)
        Los valores objetivo para la prueba.

    Notas:
    ------
    - Esta función utiliza la función `fetch_openml` de `sklearn.datasets` para obtener el conjunto de datos MNIST.
    - Si `randomize` es True, las muestras se barajan usando un estado aleatorio fijo para reproducibilidad.
    - La función `train_test_split` de `sklearn.model_selection` se utiliza para dividir los datos.
    - Si `standardize` es True, se utiliza `StandardScaler` de `sklearn.preprocessing` para estandarizar las características.
    - El escalador ajustado se guarda en un archivo llamado 'scaler.joblib' en el directorio '../models/'.
    """
    # Descargar el conjunto de datos MNIST desde OpenML
    X, y = fetch_openml('mnist_784', version=1, return_X_y=True)
    if randomize:
        # Si randomize es True, barajar las muestras
        random_state = check_random_state(0)
        permutation = random_state.permutation(X.shape[0])
        X = X[permutation]
        y = y[permutation]
    # Dividir los datos en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)
    if standardize:
        # Si standardize es True, estandarizar las características
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        # Guardar el escalador ajustado
        dump(scaler, '../models/scaler.joblib')
    return X_train, y_train, X_test, y_test

# Uso de la función fetch_data para obtener los datos
train_data, train_labels, test_data, test_labels = fetch_data()

# Crear una instancia del clasificador SVM con un kernel lineal y un estado aleatorio específico
classifier = SVC(kernel="linear", random_state=6)

# Entrenar el clasificador utilizando los datos y etiquetas de entrenamiento
classifier.fit(train_data, train_labels)

# Guardar el modelo entrenado en un archivo para uso futuro
dump(classifier, "../models/digit_recognizer")

# Utilizar el clasificador entrenado para predecir las etiquetas del conjunto de datos de prueba
prediction = classifier.predict(test_data)

# Imprimir un informe de clasificación que incluye métricas como precisión, recall y f1-score
print(f"Classification report for classifier {classifier}:\n"
      f"{metrics.classification_report(test_labels, prediction)}\n")

# Calcular la matriz de confusión
cm = metrics.confusion_matrix(test_labels, prediction)
# Visualizar la matriz de confusión
disp = metrics.ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classifier.classes_)
disp.plot()
plt.savefig('../graphs/confusion_matrix.png')  # Guardar la gráfica
plt.close()  # Cerrar la figura

n_classes = 10  # Número de clases en MNIST
# Convertir las etiquetas de prueba a formato binarizado
y_test_binarized = label_binarize(test_labels, classes=[str(i) for i in range(n_classes)])

# Calcular la función de decisión para cada clase
decision_function = classifier.decision_function(test_data)

# Calcular y trazar la curva Precision-Recall para cada clase
for i in range(n_classes):
    precision, recall, _ = metrics.precision_recall_curve(y_test_binarized[:, i], decision_function[:, i])
    plt.plot(recall, precision, lw=2, label=f'Class {i}')

plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Curva Precision-Recall por Clase')
plt.legend(loc='best')
plt.savefig('../graphs/precision_recall_curve_multiclass.png')  # Guardar la gráfica
plt.close()  # Cerrar la figura

# Convertir las etiquetas a formato numpy
train_labels = train_labels.astype(int)
test_labels = test_labels.astype(int)

# Intentar obtener los coeficientes del hiperplano
w = classifier.coef_[0]

# Agregar un pequeño valor epsilon para evitar división por cero
epsilon = 1e-10
slope = -w[0] / (w[1] + epsilon)
intercept = -classifier.intercept_[0] / (w[1] + epsilon)

# Crear una línea para el hiperplano de decisión
xx = np.linspace(min(train_data[:, 0]), max(train_data[:, 0]))
yy = slope * xx + intercept

# Crear márgenes (paralelos al hiperplano de decisión)
margin = 1 / np.sqrt(np.sum(classifier.coef_ ** 2))
yy_down = yy - np.sqrt(1 + slope ** 2) * margin
yy_up = yy + np.sqrt(1 + slope ** 2) * margin

# Plotear los datos y los hiperplanos
plt.scatter(train_data[:, 0], train_data[:, 1], c=train_labels, cmap='coolwarm', s=30)
plt.plot(xx, yy, 'k-')
plt.plot(xx, yy_down, 'k--')
plt.plot(xx, yy_up, 'k--')

# Resaltar los vectores de soporte
plt.scatter(classifier.support_vectors_[:, 0], classifier.support_vectors_[:, 1], s=100, facecolors='none', edgecolors='k')

plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.title('SVM con Kernel Lineal')
plt.savefig('../graphs/svm_hyperplane.png')  # Guardar la gráfica
plt.close()  # Cerrar la figura