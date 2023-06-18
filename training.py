import pandas as pd
import pickle
from sklearn.feature_selection import SelectKBest, f_regression,f_classif
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Importing library for testing the accuracy score
from sklearn.metrics import f1_score, accuracy_score

# Importing the classifiers
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

class MLModel():
    def __init__(self,filename) -> None:
        self.filename = filename

    def create_model(self):
        df = pd.read_csv(self.filename)
        X = df.iloc[:,:-1]
        y = df.iloc[:,-1]

        #Dividing the dataset
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if (len(X.columns)<5):
            selector = SelectKBest(f_classif,k = len(X.columns))
            selector.fit(X_train,y_train)
            selected_features= X_train.columns[selector.get_support()]
        else:
            selector = SelectKBest(f_classif,k = 5)
            selector.fit(X_train,y_train)
            selected_features= X_train.columns[selector.get_support()]


        print(selected_features)

        X_train_selected = selector.transform(X_train)
        X_test_selected = selector.transform(X_test)


        sc = StandardScaler()
        X_train_scaled = sc.fit_transform(X_train_selected)
        X_test_scaled = sc.transform(X_test_selected)   

        classifiers ={
            'Logistic Regression' : LogisticRegression(),
            'KNeighbors Classifiers' : KNeighborsClassifier(),
            'Decision Tree Classifier' : DecisionTreeClassifier()
        }
        ndic = dict()
        for key,classifier in classifiers.items():
            clf = classifier.fit(X_train_scaled,y_train)
            ndic[classifier] = accuracy_score(y_test,classifier.predict(X_test_scaled))
        del key,classifier

        # for cs,accuracy in ndic.items():
        #     print(f'{cs} : {accuracy}')
        # del cs,accuracy

        bestfit = max(ndic,key=lambda x:ndic[x])

        bestfit.fit(X_train_scaled,y_train)

        file = open('model.pkl','wb')

        li =[bestfit,selected_features,ndic]

        pickle.dump(li,file)
        file.close()

