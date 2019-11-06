import numpy as np
import keras.models
from keras.models import model_from_json
import tensorflow as tf


def init(): 
	json_file = open('./app/model/model.json','r')
	loaded_model_json = json_file.read()
	json_file.close()
	loaded_model = model_from_json(loaded_model_json)
	#load woeights into new model
	loaded_model.load_weights("./app/model/model.h5")
	print("Loaded Model from disk")
    #graph = tf.get_default_graph()

	#compile and evaluate loaded model
	loaded_model.compile(loss='mse', optimizer='rmsprop', metrics=['accuracy'])
    
	#loss,accuracy = model.evaluate(X_test,y_test)
	#print('loss:', loss)
	#print('accuracy:', accuracy)
    

	return loaded_model